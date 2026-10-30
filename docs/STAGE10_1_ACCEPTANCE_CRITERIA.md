# Этап 10.1 — критерии load-only испытания

Дата подготовки: 2026-10-31. Текущий статус: **PREPARATION_READY**. Игровой эксперимент не выполнялся, EML не установлен, игра не запускалась, игровые данные и сохранения не менялись.

## Почему изменён критерий

Публичный EMF Lua API 20 предоставляет только `world:template(component, entity)`. Он читает template-часть компонента уже существующей entity. API поиска или перечисления `TemplateResource` по GUID не найден. Создавать entity ради проверки на этом этапе запрещено.

Поэтому `UNAVAILABLE_WITHOUT_ENTITY` остаётся честным результатом прямого EMF lookup и не считается ошибкой load-only испытания. Новый критерий отвечает на более узкий вопрос: применил ли EML patch, загрузила ли игра изменённые ресурсы и продолжили ли EMF/Lua/Python Bridge работать в том же процессе.

## Три независимых уровня

### A — `EML_PATCH_APPLIED`

Требуются одновременно:

- complete install receipt с ожидаемыми build, версиями и уникальным `run_token`;
- строка `Running mod` именно для `aic_eml_humanoid`;
- `AIC_EML_TEMPLATE_READY` с тем же токеном, GUID и `npcId`;
- свежий `template_evidence_v1.txt` с тем же токеном;
- правильные patch version, template/source GUID, `npcId=2939921867`, `PlayerAlly`, model, animation и полный component fingerprint;
- совпадение model/animation нового и source ресурсов, `source_unchanged=true`;
- положительный EML lookup сразу после `create_resource`;
- `Applied N patches` с `N>0` после marker этого запуска;
- отсутствие serialization/resource/GUID errors.

Маркер Lua без последующего writer finalization не подтверждает уровень A.

### B — `GAME_LOAD_CONFIRMED`

Требуются отчёт того же `run_token` и build 1273043, достижение главного меню, загрузка только тестового LOCAL-мира, отсутствие resource/game errors, проверенный backup и post-run integrity report. Все KFC/DAT изменения должны быть перечислены и проверены; нецелевые сохранения должны остаться неизменными; rollback должен быть готов.

Успешная загрузка не подтверждает навигацию, визуальный результат, AI, lifecycle или возможность будущего spawn.

### C — `EMF_RUNTIME_CONFIRMED`

Требуются EMF 0.3.2, build 1273043, Lua host 1.9.0, marker observer с тем же `run_token`, ответы `status`, `inspect`, `compare` и успешные read-only `diagnose/status` через Python Bridge. Каждый ответ observer обязан сообщать `read_only=true`, `spawn_forbidden=true`, свой токен и:

```text
direct_emf_template_lookup=UNAVAILABLE_WITHOUT_ENTITY
```

Значения template обозначаются источником `EML_EXPORT`. Факт исполнения observer и Lua host относится к `EMF_RUNTIME`. Экспорт EML не выдаётся за независимое чтение ресурса через EMF.

## Корреляция одного запуска

Timestamp сам по себе не используется. При отдельно разрешённой установке `install()` создаёт случайный 128-битный hex `run_token` и встраивает его в копии `src/mod.lua` и observer `main.lua`. Тот же токен сохраняется в install receipt, EML evidence, EML marker, EMF observer marker и ответах observer. Отчёты game/bridge/integrity также обязаны содержать этот токен.

Репозиторий содержит только placeholder. Ручная установка исходника без его замены завершается fail-closed assertion. Несовпадение любого токена означает stale/mixed evidence и запрещает успех.

## Итоговые статусы

| Статус | Значение |
|---|---|
| `NOT_EXECUTED` | runtime-артефакты отсутствуют |
| `PREPARATION_READY` | offline preflight готов; для установки ещё нужны verified backup и разрешение пользователя |
| `PARTIAL_SUCCESS` | подтверждена только часть A/B/C либо данных недостаточно |
| `LOAD_ONLY_SUCCESS` | A, B, C и все проверки backup/source/save/rollback подтверждены |
| `FAILED` | получено явное противоречие или ошибка уровня |
| `RECOVERY_REQUIRED` | неизвестны изменения файлов/сохранений либо rollback не готов |

`load_only_success` вычисляет evaluator. Вход не содержит поля, которым можно вручную включить успех. Любое отсутствующее доказательство остаётся `null/UNKNOWN`. `spawn_ready` на этапе 10.1 всегда `false`, включая `LOAD_ONLY_SUCCESS`.

## CLI

Read-only preflight:

```powershell
.\.tools\python\python.exe -m scripts.stage10 preflight `
  --game 'D:\SteamLibrary\steamapps\common\Enshrouded' `
  --eml runtime\stage10\downloads\dbghelp.dll `
  --backup-manifest runtime\backups\stage10-pre-eml-<timestamp>\manifest.json
```

Оценка уже собранных файлов:

```powershell
.\.tools\python\python.exe -m scripts.stage10 evaluate `
  --install-receipt runtime\stage10\install-receipt.json `
  --eml-log runtime\stage10\evidence\eml.log `
  --evidence runtime\stage10\evidence\template_evidence_v1.txt `
  --emf-log runtime\stage10\evidence\emf_core.log `
  --observer-results runtime\stage10\evidence\observer-results.json `
  --bridge-diagnostics runtime\stage10\evidence\bridge-diagnostics.json `
  --game-load-report runtime\stage10\evidence\game-load-report.json `
  --backup-manifest runtime\backups\stage10-pre-eml-<timestamp>\manifest.json `
  --integrity-report runtime\stage10\evidence\integrity-report.json
```

`evaluate` ничего не устанавливает и не подключается к игре. Без входов он возвращает `NOT_EXECUTED`.

JSON-отчёты должны быть объектами. `game-load-report` содержит `run_token`, `game_build`, `main_menu_reached`, `local_test_world_loaded`, пустые `resource_errors` и `game_errors`. Bridge diagnostics содержит токен, `connected`, `diagnose_ok`, `status_ok`, EMF version/API/build и пустой `errors`. Integrity report содержит токен, пустой `unknown_changes`, подтверждения review KFC/DAT, целостности saves, неизменности нецелевых saves и готовности rollback. Отсутствующее поле остаётся UNKNOWN и не заменяется предположением.

## Что не доказано

Даже `LOAD_ONLY_SUCCESS` не доказывает прямой EMF lookup, spawnability, правильный внешний вид сущности, faction конкретного экземпляра, ownership, движение, бой, inventory/equipment, persistence и безопасный dismiss. Он не меняет allow-list, IdentityGate, `runtime.lock`, recovery или права `aic_body`.

Следующий шаг после `LOAD_ONLY_SUCCESS` — отдельное техническое ревью результатов и новый этап подготовки одного контролируемого spawn. Для него требуется отдельное явное разрешение пользователя.
