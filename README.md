# enshrouded-ai-companion

**Текущий приоритет — настоящий второй игровой персонаж.** Этап 7 установил: EMF не предоставляет подтверждённого API создания второго player slot без клиента; визуальная копия не является полноценным игроком; наиболее реалистичный путь — отдельный штатный клиент с отдельным account authority. Этот путь даёт настоящий inventory/equipment/progress, но AI-управление вторым клиентом пока не подтверждено и отключено. Исследование: [PLAYER_CHARACTER_COMPANION_RESEARCH.md](docs/PLAYER_CHARACTER_COMPANION_RESEARCH.md), архитектура: [PLAYER_CHARACTER_COMPANION_ARCHITECTURE.md](docs/PLAYER_CHARACTER_COMPANION_ARCHITECTURE.md).

**Текущее направление:** человекоподобный AI Companion. Исследованы 18 реальных workshop survivor templates, варианты player clone и отдельного humanoid body. Безопасный runtime spawn гуманоида пока заблокирован: uniqueness, начальная faction, ownership и dismiss независимого экземпляра не подтверждены. Выводы — [HUMAN_COMPANION_RESEARCH.md](docs/HUMAN_COMPANION_RESEARCH.md), контракты — [HUMAN_COMPANION_ARCHITECTURE.md](docs/HUMAN_COMPANION_ARCHITECTURE.md).

**Первое игровое испытание:** `emf.spawn` создал Vukah, но fingerprint отсутствовал; faction не была изменена, NPC оказался враждебным. Сценарий остановлен, тестовые LOCAL-сохранения восстановлены и проверены. Vukah отложен как `legacy_vukah`; результат не переписывается — [FIRST_INGAME_TEST.md](docs/FIRST_INGAME_TEST.md).

**Техническое состояние этапа 6:** 97 офлайн-тестов PASS, `safety_revision=2` не ослаблена. Реализованы только каталог human candidates, evidence-aware capabilities и fail-closed IdentityGate; ни одна игровая команда гуманоида не включена. Актуальные проверки и SHA-256 пакета — [TEST_RESULTS.md](docs/TEST_RESULTS.md).

**Этап 3: подготовка первого игрового испытания.** [Проверка установленной игры, резервная копия и пошаговый запуск](docs/STAGE3_PREFLIGHT.md). EXE соответствует сборке EMF 1273043. Body Adapter — Lua-мод, собственной DLL у него нет. Игровое испытание ещё не выполнялось.

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

Следующий этап — отдельно согласованный **read-only** survey компонентов/model двух assistant templates. Spawn остаётся запрещённым до выбора тела и разработки protocol revision 3.
