# Этап 10 — план загрузки собственного template

## Дополнение этапа 10.3

План 10.1/10.2 ниже сохранён как история. Текущий patch 0.2.0 пишет `template_evidence_v2.txt` с typed model status. Повторная установка и load-only проверка **BLOCKED** до отдельного разрешения; даже технически успешная запись `MISSING/component_missing` должна дать FAIL уровня A. Для PASS нужен реальный подтверждённый model dependency, а не ослабление evaluator.

Перед возможным повтором требуется новый verified backup и обычный install receipt с новым run token. Игра запускается только пользователем. Spawn и любые runtime mutations остаются запрещены.

Текущий статус: **PREPARATION_READY; игровой эксперимент НЕ ВЫПОЛНЯЛСЯ**. Этап 10.1 принимает `UNAVAILABLE_WITHOUT_ENTITY` как известное ограничение и оценивает три независимых уровня A/B/C. До установки всё равно нужны новый verified backup и отдельное разрешение пользователя.

## Preflight

Подготовлен `python -m scripts.stage10 preflight`, всегда read-only. Фактический dry-run 2026-10-31 подтвердил:

- точный путь `D:\SteamLibrary\steamapps\common\Enshrouded`;
- закрытый процесс Enshrouded на момент ручной проверки;
- build 1273043 и SHA-256 EXE;
- установленный официальный EMF `dinput8.dll`;
- официальный EML `dbghelp.dll` с release digest;
- отсутствие существующего `dbghelp.dll`, `eml.json`, EML `mods`, stale evidence и `enshrouded.kfc.bak`;
- patch и observer проходят offline validation;
- baseline содержит `enshrouded_000.dat` … `enshrouded_054.dat`.

Dry-run возвращает `PREPARATION_READY`, фактическое состояние backup, `installation_ready`, blockers и `requires_user_approval=true`. `phase_b_allowed=false` остаётся границей авторизации: preflight не является разрешением пользователя.

## Backup перед фазой B

Backup ещё не создавался. Dry-run плана: 20 файлов, 224 556 422 байта. В него входят:

- `enshrouded.kfc` — 9 392 128 байт, SHA-256 `54a8cb76b3229c486ef55a7ababcd48828fa0ffc5bb144d206f687fd0ab00a92`;
- `enshrouded.kfc_resources` — 214 536 192 байта, SHA-256 `53786c45797d275661f3ccc1fd8c84527a74f376e01f05fc76351f91fb17cb3d`;
- весь малый LOCAL-каталог `default`: `character0.ksd`, `world0.ksd` и штатные backup slots.

В LOCAL `default` найден ровно один текущий `character0.ksd` и один `world0.ksd`; пользователь ранее определил их как `Body Test` и `AI Body Test`. Формат KSD не разбирался, поэтому перед фазой B имена нужно ещё раз визуально подтвердить в меню и основной Steam-мир не открывать.

Будущая копия создаётся в новом `runtime/backups/stage10-pre-eml-<timestamp>/`. Manifest содержит source/backup path, bytes, mtime_ns, SHA-256, причину включения и `verified=true`; после копирования каждый файл читается повторно. Любой mismatch блокирует установку.

## Установка после отдельного разрешения

План добавляет только:

```text
<game>/dbghelp.dll
<game>/eml.json
<game>/mods/aic_eml_humanoid/{mod.json,README.md,src/mod.lua}
<game>/emf/mods/aic_template_observer/{mod.json,main.lua,json.lua}
<game>/emf/config/aic_template_observer.ini
```

`eml.json` включает export и не включает console. `dinput8.dll` не меняется. Существующий `aic_body` и остальные EMF-моды не переписываются. Любой destination collision, повторная/частичная установка или неверный backup останавливает процесс. Install receipt записывает hash каждого добавленного файла после каждого шага, чтобы частичную установку можно было убрать без угадывания.

При реальной установке создаётся случайный `run_token`, который встраивается в EML patch и observer. Он связывает receipt, evidence и оба журнала одного запуска. Исходники с placeholder вручную не запускаются: Lua assertions откажут загрузку.

Официальный `emm.exe` в игру не копируется и для proxy-сценария не запускается.

## Запуск и диагностика

Эти действия не выполнялись:

1. Пользователь вручную запускает Steam/Enshrouded.
2. Использует только LOCAL `Body Test` / `AI Body Test` после визуального подтверждения.
3. Никаких spawn/destroy/faction/inventory команд.
4. Проверяются EML logs, `AIC_EML_TEMPLATE_READY`, `Applied N patches`, свежий evidence и отсутствие ошибок.
5. Через bridge выполняются только:

```text
aic_template_observer.status
aic_template_observer.inspect
aic_template_observer.compare
```

6. Дополнительно выполняются существующие read-only `companion diagnose/status`; `aic_body.request` запрещён.
7. Игра штатно закрывается. Сравниваются KFC/resources, список DAT, EML/EMF logs и LOCAL save hashes.

Observer возвращает model/animation/component/faction/npcId из EML evidence, отдельно сопоставляет model/animation с source и группирует фактически перечисленные component types по navigation/inventory/equipment/save/network. Отсутствующее поле получает `UNAVAILABLE`; источник полей обозначается `EML_EXPORT`. Он также возвращает ограничение `UNAVAILABLE_WITHOUT_ENTITY`: публичный EMF Lua не может искать template GUID без entity. Внешняя проверка объединяет evidence с `Applied N patches`; сам observer не называет pending writer успешным.

## Критерии успеха 10.1

Evaluator независимо подтверждает:

- **A / `EML_PATCH_APPLIED`:** exact mod, run token, новый resource fingerprint, неизменный source, marker и writer finalization без ошибок;
- **B / `GAME_LOAD_CONFIRMED`:** меню и LOCAL test world загрузились на том же build/token, resource errors отсутствуют, backup/save/file integrity и rollback подтверждены;
- **C / `EMF_RUNTIME_CONFIRMED`:** EMF/Lua/observer/Python Bridge работают на том же token, все три read-only команды отвечают.

Только A+B+C и обязательные safety checks дают `LOAD_ONLY_SUCCESS`. Прямой EMF lookup не требуется и остаётся отдельным `UNAVAILABLE_WITHOUT_ENTITY`. `LOAD_ONLY_SUCCESS` никогда не включает `spawn_ready`.

## Критерии остановки

- антивирус блокирует/карантинит файл;
- hash/path/build/loader отличается;
- EML/EMF loader error или DLL conflict;
- source template/component отсутствует;
- GUID collision, serialization error, `Applied 0 patches`;
- evidence отсутствует, старый, malformed или содержит неверный GUID/npcId/faction;
- model/animation `UNAVAILABLE`, source изменён или component fingerprint неполон;
- observer/bridge недоступен;
- изменился существующий DAT или появились неизвестные outputs;
- изменились нецелевые сохранения;
- любое предложение spawn для обхода read-only ограничения.

## Rollback

1. Закрыть игру; подтвердить отсутствие процесса.
2. Сохранить диагностические logs вне игрового каталога с учётом приватности.
3. Сверить install receipt: added files удаляются только при совпадении текущего hash с receipt. При foreign change rollback останавливается.
4. Проверить backup manifest и hashes.
5. Восстановить `enshrouded.kfc` и `enshrouded.kfc_resources` через временный файл и atomic replace.
6. Удалить `enshrouded.kfc.bak` только если его hash равен исходному KFC.
7. Каждый новый `enshrouded_NNN.dat` должен быть явно перечислен после post-run review; неизвестные additions блокируют автоматический rollback.
8. Не трогать существующие DAT, EMF mods или основные сохранения.
9. Повторно проверить hashes и создать `rollback-report.json`; незавершённый откат оставляет report в состоянии `in_progress`.

Реализация `restore_game_data` протестирована на временных каталогах и по умолчанию работает как dry-run. Она не запускалась на игре.

## Оставшиеся ограничения

Прямой EMF lookup по GUID остаётся недоступен без entity, но после пересмотра критерия он не блокирует load-only испытание. До реального теста остаются неизвестны совместный runtime EML+EMF, writer/game load и сохранность post-state.

Эксперимент готов к отдельному согласованию только после фактического создания и проверки нового backup и визуального подтверждения LOCAL `Body Test` / `AI Body Test`. Установка и запуск в этапе 10.1 не выполняются.

Полные правила и форматы evaluator: [STAGE10_1_ACCEPTANCE_CRITERIA.md](STAGE10_1_ACCEPTANCE_CRITERIA.md).

## Действия пользователя при отдельно согласованном запуске

1. Явно разрешить только этап 10.1: создание verified backup, установку EML/patch/observer и последующий rollback без spawn.
2. Дождаться отчёта Codex `installation_ready=true`; до него игру не запускать.
3. Самостоятельно запустить Enshrouded через Steam и сообщить, когда открыто главное меню.
4. В меню визуально выбрать только LOCAL-персонажа `Body Test` и LOCAL-мир `AI Body Test`; при несовпадении имён остановиться.
5. Загрузить мир и сообщить об успешной загрузке. Не открывать консоль, не выполнять spawn/destroy/faction/inventory команды и не активировать `aic_body`.
6. Пока мир открыт, дождаться завершения read-only observer/bridge диагностики Codex.
7. Штатно выйти в меню, закрыть игру и сообщить `закрыл`.
8. Не запускать игру повторно до post-run integrity check, evaluator и согласованного rollback.

Codex в этой последовательности не запускает игру: он проверяет backup/install, выполняет только read-only диагностику, оценивает A/B/C и при закрытой игре проводит точный rollback по receipt/manifest.
