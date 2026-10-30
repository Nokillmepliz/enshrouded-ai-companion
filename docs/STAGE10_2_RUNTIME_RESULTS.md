# Этап 10.2 — runtime-результаты Humanoid Template

Дата начала: 2026-10-31. Текущая контрольная точка: **INSTALLATION_READY — WAITING_FOR_MANUAL_GAME_START**.

Часть B выполнена после явного разрешения пользователя. Новый verified backup создан, EML/patch/read-only observer установлены и проверены. Игра не запускалась. Результат evaluator остаётся `NOT_EXECUTED`; `spawn_ready=false`.

## Разрешение и граница действий

ТЗ этапа 10.2 сначала разрешило read-only часть A. Затем пользователь отдельно разрешил часть B точной формулировкой: создать verified backup и установить EML, humanoid patch и read-only observer, игру не запускать. Spawn, destroy, faction, ECS, inventory, equipment и save mutations не выполнялись.

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

Создан новый backup `stage10-pre-eml-20261030T220012Z`: 20 файлов, 224 556 422 байта. Все копии повторно прочитаны; SHA-256 источников и копий совпали, mismatch 0. Manifest повторно прошёл `verify_backup`, а текущие источники после копирования совпали с записанными размерами и hashes. Состояние: `backup_verified=true`, `rollback_ready=true`.

## Dry-run установки и отката

План установки содержит ровно девять файлов: проверенный `dbghelp.dll`, новый `eml.json`, три файла EML patch, три файла observer и его отдельную INI-конфигурацию. `dinput8.dll`, `aic_body`, остальные EMF-моды и пользовательские конфигурации в план не входят.

До разрешения dry-run установки без нового manifest останавливался с `verified_backup_required`. После создания backup существующий installer добавил ровно девять запланированных файлов. Receipt имеет `state=complete`, 9/9 текущих hashes совпадают; временных `*.stage10-install` нет.

Run correlation token этого испытания:

```text
69a6a5ff13e66c37614e212790464271
```

Токен присутствует в установленных EML patch и observer, repository placeholders сохранены, а в установленных копиях placeholder отсутствует. GUID template присутствует. `dbghelp.dll` совпадает с закреплённым SHA-256; `dinput8.dll` не изменился. `eml.json`: console выключена, export включён. Observer включён своей новой INI-конфигурацией. Microsoft Defender и real-time protection оставались включёнными; блокировок не возникло.

`aic_body` не входит в receipt и не изменялся. Дополнительная сверка обнаружила ранее установленный legacy `body.lua`, не совпадающий с поздней repository-версией с `body_profiles.lua`; установленный `main.lua` совпадает. Это предварительно существовавшее состояние первого Vukah-теста, оно не исправлялось и не используется для spawn. На load-only этапе разрешены только read-only `diagnose/status`; `aic_body.request` запрещён.

Создан игнорируемый Git pre-run baseline: install/manifest hashes, корневой список и metadata 55 существующих DAT. Копирование 51,5 ГБ DAT не выполнялось. После запуска новые/изменённые DAT будут сопоставлены с baseline и отдельно проверены.

## Runtime и evaluator

| Уровень | Результат |
|---|---|
| A — `EML_PATCH_APPLIED` | `UNKNOWN / NOT_EXECUTED` |
| B — `GAME_LOAD_CONFIRMED` | `UNKNOWN / NOT_EXECUTED` |
| C — `EMF_RUNTIME_CONFIRMED` | `UNKNOWN / NOT_EXECUTED` |
| Новый `TemplateResource` | не подтверждён |
| Faction 11 / source unchanged | runtime не подтверждён |
| Save integrity после запуска | ещё не проверялась, запуска не было |
| Rollback | `NOT_EXECUTED` |
| Итог | `NOT_EXECUTED`, `load_only_success=false`, `spawn_ready=false` |

## Следующая контрольная точка

Часть B завершена. Текущий статус:

```text
INSTALLATION_READY — WAITING_FOR_MANUAL_GAME_START
```

Игру теперь запускает только пользователь через Steam. Нужно визуально выбрать LOCAL-персонажа `Body Test`, LOCAL-мир `AI Body Test`, загрузить мир один раз и сообщить «загрузился». Нельзя выполнять spawn или другие команды модификации. При вылете, зависании или необычной ошибке нужно закрыть игру и сообщить, не повторяя запуск.
