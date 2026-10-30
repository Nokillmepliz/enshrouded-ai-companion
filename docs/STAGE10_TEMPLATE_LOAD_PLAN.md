# Этап 10 — план загрузки собственного template

Текущий статус: **ФАЗА A ЗАВЕРШЕНА; ФАЗА B НЕ ВЫПОЛНЯЛАСЬ И ПОКА BLOCKED ПОЛНЫМ КРИТЕРИЕМ EMF LOOKUP**.

## Preflight

Подготовлен `python -m scripts.stage10`, всегда read-only. Фактический dry-run 2026-10-31 подтвердил:

- точный путь `D:\SteamLibrary\steamapps\common\Enshrouded`;
- закрытый процесс Enshrouded на момент ручной проверки;
- build 1273043 и SHA-256 EXE;
- установленный официальный EMF `dinput8.dll`;
- официальный EML `dbghelp.dll` с release digest;
- отсутствие существующего `dbghelp.dll`, `eml.json`, EML `mods`, stale evidence и `enshrouded.kfc.bak`;
- patch и observer проходят offline validation;
- baseline содержит `enshrouded_000.dat` … `enshrouded_054.dat`.

Dry-run намеренно возвращает `phase_b_allowed=false`. Он не является установщиком и не выражает согласие пользователя.

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

## Критерии успеха

Частичный runtime-успех load-only:

- EML и EMF стартовали вместе;
- writer завершился;
- игра дошла до меню/LOCAL test world без asset errors;
- evidence подтверждает новый resource и неизменность source;
- EMF Lua observer и Python Bridge доступны;
- KFC/save post-state объясним и rollback dry-run проходит.

Полный критерий исходного ТЗ дополнительно требует прямого обнаружения resource через EMF. Он сейчас технически недоступен без entity или нового native read-only API, поэтому фаза B не может дать полный ответ на главный вопрос в текущем виде.

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

## Оставшийся блокер

Для полного критерия нужен один из двух вариантов:

1. подтверждённое новое read-only EMF API `get_template_resource(guid)`/enumeration, либо
2. явное изменение критерия этапа: принять EML positive evidence + успешный game load + работающий EMF observer/bridge как достаточное доказательство доступности данных процессу.

До решения этого пункта запрос на фазу B не выдаётся.
