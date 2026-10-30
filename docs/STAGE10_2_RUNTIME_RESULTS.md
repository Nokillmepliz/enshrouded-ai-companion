# Этап 10.2 — runtime-результаты Humanoid Template

Дата начала: 2026-10-31. Текущая контрольная точка: **PART A COMPLETE — PREPARATION_READY — WAITING FOR PART B APPROVAL**.

Игровой эксперимент ещё не выполнялся. EML не установлен, verified backup этапа 10.2 не создан, игра не запускалась, `run_token` и install receipt отсутствуют. Результат evaluator остаётся `NOT_EXECUTED`; `spawn_ready=false`.

## Разрешение и граница действий

ТЗ этапа 10.2 разрешило read-only часть A. Оно отдельно требует нового явного разрешения перед частью B, поэтому копирование backup и файлов в каталог игры не выполнялось. Spawn, destroy, faction, ECS, inventory, equipment и save mutations не выполнялись.

## Read-only preflight

Усиленный фактический preflight завершился `PREPARATION_READY`:

| Проверка | Результат |
|---|---|
| Процесс Enshrouded/server | отсутствует |
| Build | `1273043` |
| `enshrouded.exe` SHA-256 | `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882` |
| EMF `dinput8.dll` SHA-256 | `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee` |
| EML `dbghelp.dll` SHA-256 | `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa` |
| Patch | offline validation PASS, fixed GUID/source/faction/npcId/run correlation, no runtime/save paths |
| Observer | offline validation PASS, disabled by default, read-only, `status/inspect/compare` |
| Existing `dbghelp.dll` / `eml.json` | отсутствуют |
| `enshrouded.kfc.bak` | отсутствует |
| Сторонние EML-моды | отсутствуют |
| Stale evidence | отсутствует |
| Stage 10 install temp/receipt | отсутствуют |
| Observer install/config collision | отсутствует |
| Baseline DAT | `enshrouded_000.dat`–`enshrouded_054.dat` |
| Свободно на диске игры | 434 613 178 368 байт |
| Минимум preflight | 1 297 670 144 байт |

В установленном EMF включены `lua` и существующий `aic_body`; остальные комплектные моды выключены. Этап 10.2 не менял эту конфигурацию и не активировал основной Body Adapter. Будущий observer добавляется отдельной конфигурацией и не вызывает `aic_body.request`.

## Backup и LOCAL scope

Текущий dry-run повторно определил 20 файлов и 224 556 422 байта: два игровых KFC/resources и 18 файлов из изолированного LOCAL-набора. В LOCAL-наборе ровно один текущий `character0.ksd` и один текущий `world0.ksd`; их связь с `Body Test` / `AI Body Test` ранее подтверждена пользователем и зафиксирована в результате первого игрового теста. Формат KSD офлайн не декодировался, поэтому при ручном запуске имена снова проверяются визуально.

Две старые копии этапов 3/5 используют другой manifest format и намеренно не принимаются Stage 10 verifier. Обнаруженный при этой проверке `AttributeError` исправлен: несовместимый manifest теперь безопасно возвращает `False`. Для части B обязателен новый каталог `runtime/backups/stage10-pre-eml-<timestamp>/`.

Состояние сейчас: `backup_verified=false`, `rollback_ready=false`, `installation_ready=false`. Единственный operational blocker — `verified_backup_missing` плюс отсутствующее разрешение на часть B.

## Dry-run установки и отката

План установки содержит ровно девять файлов: проверенный `dbghelp.dll`, новый `eml.json`, три файла EML patch, три файла observer и его отдельную INI-конфигурацию. `dinput8.dll`, `aic_body`, остальные EMF-моды и пользовательские конфигурации в план не входят.

Dry-run установки без нового manifest остановлен с `verified_backup_required`. Dry-run отката без install receipt остановлен с `rollback_receipt_invalid`. Это ожидаемое fail-closed поведение. Реальные install/rollback операции не выполнялись.

## Runtime и evaluator

| Уровень | Результат |
|---|---|
| A — `EML_PATCH_APPLIED` | `UNKNOWN / NOT_EXECUTED` |
| B — `GAME_LOAD_CONFIRMED` | `UNKNOWN / NOT_EXECUTED` |
| C — `EMF_RUNTIME_CONFIRMED` | `UNKNOWN / NOT_EXECUTED` |
| Новый `TemplateResource` | не подтверждён |
| Faction 11 / source unchanged | runtime не подтверждён |
| Save integrity после запуска | не проверялась, запуска не было |
| Rollback | `NOT_EXECUTED` |
| Итог | `NOT_EXECUTED`, `load_only_success=false`, `spawn_ready=false` |

## Следующая контрольная точка

После отдельного явного разрешения на часть B Codex должен при закрытой игре создать и повторно проверить новый backup, установить только девять перечисленных файлов, сверить receipt/hashes/token и остановиться с сообщением:

```text
INSTALLATION_READY — WAITING_FOR_MANUAL_GAME_START
```

Игру после этого запускает только пользователь. Разрешение части B не является разрешением на автоматический запуск игры, spawn или повторный игровой запуск.
