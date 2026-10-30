# Этап 10.2 — результат первого load-only запуска Humanoid Template

Дата испытания: 2026-10-31. Итог evaluator: **`FAILED`**. Уровень B подтверждён, уровень A отклонён, уровень C остался неполным. `load_only_success=false`, `spawn_ready=false`, следующий этап заблокирован.

## Границы испытания

Пользователь вручную запустил Enshrouded через Steam и загрузил LOCAL-персонажа `Body Test` в LOCAL-мир `AI Body Test`. Codex выполнял только чтение состояния через EMF Bridge и сбор журналов. Команды spawn/destroy/faction/ECS/inventory/equipment не выполнялись. Игра закрыта пользователем; процесс `enshrouded.exe` после закрытия отсутствует.

Run token: `69a6a5ff13e66c37614e212790464271`. Сборка игры: `1273043`. EMF: `0.3.2`, API 20. EML: официальный проверенный `dbghelp.dll` с SHA-256 `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa`.

## Результаты A/B/C

| Уровень | Результат | Доказательство |
|---|---|---|
| A — `EML_PATCH_APPLIED` | **FAIL** | EML загрузил `aic_eml_humanoid`, вывел коррелированный READY marker и `Applied 1 patches`, но export содержит `model_guid=nil` и `source_model_guid=nil`. Это не является подтверждённым model fingerprint. |
| B — `GAME_LOAD_CONFIRMED` | **PASS** | EMF зафиксировал главное меню, загрузку LOCAL-мира и сохранения; Bridge показал running world `AI Body Test`, LOCAL character `Body Test`; в game/EMF-журналах нет resource/game errors. |
| C — `EMF_RUNTIME_CONFIRMED` | **UNKNOWN** | EMF 0.3.2, build 1273043, 50/50 signatures, Lua и observer загрузились; `status` и `compare` получены. Ответ `inspect` был обрезан EMF на 1023 байтах и не разобрался как JSON. |

Положительно подтверждены GUID нового template и source, `npc_id=2939921867`, `faction=PlayerAlly`, одинаковый animation graph, component clone, `source_unchanged=true`, resource lookup после создания и финализация writer по `Applied 1 patches`. Однако одинаковые строковые значения `nil` раньше ошибочно считались доступной моделью. После исправления evaluator корректно отклоняет этот результат.

Direct lookup template GUID через public EMF Lua остаётся `UNAVAILABLE_WITHOUT_ENTITY`; это известное ограничение, а не доказательство отсутствия template. Новый template не спавнился, поэтому его визуальная модель, самостоятельность экземпляра, ownership и dismiss не проверены.

## Целостность и runtime outputs

Verified backup `stage10-pre-eml-20261030T220012Z` повторно проверен: 20/20 копий совпадают с manifest. Все 9 установленных файлов совпадают с install receipt. Исходные DAT `000–054` не менялись по размеру и mtime.

EML создал ожидаемые и атрибутированные outputs:

- `enshrouded.kfc.bak`, чей SHA-256 совпадает с backup исходного KFC;
- изменённые `enshrouded.kfc` и `enshrouded.kfc_resources`;
- нулевые последовательные DAT `055–063` с timestamp применения patch;
- `.cache` с `types.json` и Lua definition files, прямо перечисленными в EML log;
- `export` с evidence и `logs` с журналом EML.

Неатрибутированных изменений нет. LOCAL-профиль штатно изменил `character0.ksd`, `world0.ksd` и две ротационные копии мира после загрузки/сохранения; все исходные версии остаются в проверенном backup. Steam-сохранения не использовались и инструменты этапа к ним не писали.

Dry-run отката принят: восстановить оба KFC из verified backup, удалить `enshrouded.kfc.bak` и только явно перечисленные DAT `055–063`, затем удалить девять файлов по receipt. Реальный откат **не выполнен**, поскольку для него требуется отдельное разрешение пользователя. `.cache`, `export` и `logs` также являются известными EML outputs; решение об их удалении будет включено в конкретный план отката.

## Исправления после испытания

- Python evaluator и Lua observer теперь считают `nil`, `null`, `none`, пустую строку и `UNAVAILABLE` отсутствующим fingerprint; совпадение двух отсутствующих значений не проходит.
- Parser writer finalization поддерживает реальные JSON-escaped `\t` из EML log.
- Проверка Lua host принимает фактический marker `[lua] ready` EMF 0.3.2.
- `inspect` сокращён: вместо полных массивов компонентов передаются compact fingerprint и количества групп, чтобы не превышать лимит строки EMF.
- Добавлены регрессионные тесты. Полный offline suite: **188 PASS**.

Эти изменения внесены только в репозиторий. Установленные Lua-копии после игры не менялись, повторный запуск не выполнялся.

## Вердикт

```text
FAILED
A=false
B=true
C=unknown
load_only_success=false
spawn_ready=false
next_stage_allowed=false
rollback_ready=true
rollback_executed=false
```

Следующее допустимое действие — отдельно разрешённый безопасный откат. Повторное load-only испытание возможно лишь после отката, подготовки новой установки исправленного observer и решения проблемы `model_guid=nil`. Spawn остаётся запрещённым.
