# Stage 10.12 — установка Discovery и проверка persistence

2026-11-22: **POST_CLOSE_INTEGRITY_PASS_PROFILE_FOUND**. Ниже сохранены этапы
подготовки и выполненный read-only тест; повторный запуск здесь не предлагается.

Свежий closed preflight подтвердил отсутствие игры/сервера, Steam build26430625,
depot7226436020230696061 и точное совпадение 246 game/23 LOCAL записей с последним
post-close baseline120850…. Проверены hashes и metadata, а не только номера версий.

Создана новая резервная копия всех 23 LOCAL-файлов, 637831 bytes:
`C:\Enshrouded-ai-companion\runtime\backups\stage10_12-discovery-local`.
Все SHA-256 копий сверены; backup manifest:
`dc2fa0d55b1f93806779299a8470e900297947bf8f0a187d192efac0a54881fe`.
Старые backup/quarantine не менялись.

Аддитивно установлены только пять новых файлов в
`D:\SteamLibrary\steamapps\common\Enshrouded`:

- `emf/mods/aic_companion_movement/mod.json`
- `emf/mods/aic_companion_movement/main.lua`
- `emf/mods/aic_companion_movement/controller.lua`
- `emf/mods/aic_companion_movement/README.md`
- `emf/config/aic_companion_movement.ini`

Версия0.1.0; config включает мод (`enabled=1`), но main.lua сохраняет
`allow_move=false`. Исходный mod.json остаётся disabled-by-default; действует
отдельный штатный config override. README описывает офлайн-подготовку исходников;
фактическое установленное состояние фиксируется этим отчётом и receipt.

Проверены 5/5 установленных хешей, неизменность всех прежних 246 game-файлов
(включая оригиналы/shadow, Spawn Controller, SPENT, observer/content), всех
23 LOCAL записей и всех112 файлов истории, включая spawn-intent.
Новый pre-runtime inventory251/23:
`9efbdf467f494e57b6938c8923b139b62b9ff0c612a3dae3edd5d5948a48a90f`,
`runtime/stage10_12/discovery-install/inventory-after.json`.

[Exact manifest](../compatibility/experiments/stage10_12/discovery-install/manifest.json)
SHA256 `5e0c7b2e60a627c6976a7098b726894a267632a4dea7839a50a5df13fd349003`;
[receipt](../compatibility/experiments/stage10_12/discovery-install/receipt.json).
Скрипт установки exclusive-create, без overwrite/cleanup/rollback; повторный запуск
запрещён конфликтом существующих файлов. На ошибке сохраняет частичный журнал.

22/22 целевых теста повторно PASS,0failures/errors,0.023s. Полный suite не повторяли.
Игру/сервер/Bridge не запускали. Spawn, move_to, destroy и rollback не выполняли.

## Действия пользователя

Вручную запустить игру и загрузить **LOCAL Body Test / AI Body Test, slot1/1**.
Сообщить «загрузился». После проверки контекста выполнить read-only команду:

```powershell
$gameProcess = @(Get-Process -Name enshrouded -ErrorAction Stop)
if ($gameProcess.Count -ne 1) { throw 'Expected exactly one Enshrouded client' }
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\companion_movement.py' --pid $gameProcess[0].Id discover
```

Клиент проверяет hello/state, LOCAL slot/name, версии/набор модов и session.
FOUND_ONE вернёт position/home/AI state/decision/component flags. Это профиль,
не доказательство GUID/generation. NOT_FOUND/AMBIGUOUS или ошибка — остановиться,
не создавать замену и не вызывать movement. Идентификатор6959 не фиксируется.

После read-only проверки пользователь закрывает игру и сообщает «закрыл».
Затем короткий post-close audit относительно нового inventory: неизменность
исходных ресурсов/модов/latch/history, атрибуция логов, список autosave изменений
без восстановления. Результат, отчёт и код установки публикуются в GitHub после
этого этапа. Пока runtime результат и сохранение NPC после reload неизвестны.

## Полученный runtime результат

Пользователь загрузил игру PID437520; адресные Bridge hello/state подтвердили
LOCAL slot1/1 и ожидаемый набор модов. Затем пользователь самостоятельно выполнил
discover и прислал вывод: **FOUND_ONE**,count1,entity1025,npc2939921867,faction11.
Position=(3692.313232421875,893.5,1278.689697265625),
home=(3698.940673828125,893.6009521484375,1280.66357421875).
Компоненты ai/common/saved/walker присутствуют. AI state13=WaitingCloseToPlayer,
decision3=WantsToInteract по enum существующего EMF source.

[Сохранённый вывод пользователя](../compatibility/experiments/stage10_12/discovery-user.json)
явно отмечен как USER_PASTED_LOCAL_CLI_OUTPUT; агент не повторял discover.
После reload найден один совпадающий профиль, но GUID/generation не подтверждены,
строгая непрерывность идентичности прежнего entity6959 не установлена. Наличие
decision не означает выполненного взаимодействия. Движение/spawn/destroy не
вызывались. Ожидается ручное закрытие игры, затем аудит и GitHub публикация.

## Завершённый post-close audit PID437520

Пользователь закрыл игру. `audit_companion_discovery_closed.py` завершился exit0,
POST_CLOSE_INTEGRITY_PASS_PROFILE_FOUND. Свежая полная проверка SHA-256:
originals67/67, shadow77/77 и installed28/28 без изменений; LOCAL backup23/23
повторно проверен. Все112 файлов истории, spawn-intent и SPENT сохранены.

Post_close_v2 подтвердил точный перенос предыдущего игрового лога в архив и
изменение только mtime прежнего пустого chain_status. Остальные game changes —
четыре текущих лога; неизвестных изменений нет. В текущем логе ровно одна
консольная команда `aic_companion_movement.discover`; SPAWN_ATTEMPT отсутствует.
Лог подтверждает запуск нового мода и14 событий world saved slot0x0001.

LOCAL23: добавлений/удалений нет,8 файлов изменили content,9 — metadata
(дополнительно local_settings.json). Имена Body Test/AI Body Test сохранены.
Это наблюдаемые изменения autosave, не доказательство семантической целостности
всех данных. Восстановление/редактирование saves не выполнялось.

[Результат аудита](../compatibility/experiments/stage10_12/post-close.json).
Новый baseline252 game/23 LOCAL:
`runtime/stage10_12/session437520/post-close/inventory.json`, SHA-256
`90164f817c4ac2bbf1f1a48876a1aee8bb381e4ffe91844ede392c0281585d32`.
Сырые логи и backup остаются приватными. Публикуются manifest/receipt, вывод
пользователя с provenance, результаты аудита и скрипты.

Итог: read-only Discovery работает; после перезапуска найден один NPC ожидаемого
профиля, entity1025. GUID/generation instance не доказаны, movement не проверен.
allow_move=false и spawn_ready=false. Дальнейшее включение движения требует
отдельного разрешения; новые NPC, destroy, rollback не выполнялись.
