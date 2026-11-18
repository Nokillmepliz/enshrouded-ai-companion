# Stage 10.10.1 Phase F — load-only validation

## Итог после ручного закрытия, 2026-11-18

**BLOCKED_CONTENT_BUILD / LOAD_ONLY_UNCONFIRMED. `spawn_ready=false`.**
Phase F завершена фиксацией неудачного load-only теста, без исправления установки.
Причина: `AIC_PATCH:graph_changed`, content exit code2. Загрузчик явно сообщил,
что игра продолжает работу без построенного content. Успешная загрузка мира
пользователем не подтверждает загрузку clone.

Post-run аудит выполнен в `2026-11-18T12:42:29.466128+00:00`, game/server закрыты,
Steam build прежний. [Метаданные результата](../compatibility/migration/1287369/phase_f/post-close.json),
[read-only скрипт](../scripts/audit_phase_f_closed.py).

- 67/67 оригинальных ресурсов: SHA-256, размер, file identity и mtime прежние;
  EXE, KFC/resources и все64 DAT сохранены. У EXE+55 base DAT ожидаемо стало
  по две hardlink-ссылки; shadow имеет те же file IDs. Остальные9 DAT и root
  KFC/resources имеют одну ссылку. Reparse points и неожиданные связи не обнаружены.
- 16/16 установленных файлов и immutable receipt совпадают с pinned plan;
  package также проверен. Clean backup27/27 повторно проверен по SHA-256.
- Shadow содержит66 файлов:56 base links,3 private index-файла (включая KFC.bak),
  3 копии мода,3 cache-файла и state. Хеши private KFC/KFC.bak/resources совпали
  с исходной базой, копии мода — с установленными. Private files имеют одну ссылку
  и не разделяют file identity с оригиналами. Это проверка файлов, не успешной
  сериализации clone. Generated DAT отсутствует; семантический readback не проводился.
- Game inventory222 против153 до запуска:69 добавлений (66 shadow, content.log,
  file_opens.log и архив game log), удалений нет. Из прежних файлов содержимое
  поменялось только у трёх логов; chain_status.txt изменил metadata, но не содержимое.
- LOCAL inventory23: добавлений/удалений нет;17 файлов сохранили содержимое.
  Изменились `character0.ksd`, `world0.ksd` и их `backup-0`/`backup-1` (всего6).
  `local_settings.json` изменил metadata при прежнем SHA. До/после SHA и размеры
  шести файлов опубликованы в metadata без содержимого сохранений. Эти изменения
  произошли за сеанс ручного запуска, агент saves не писал. Внутренняя целостность
  и точная семантика изменений KSD не установлены; сохранения не восстанавливались.

Core log подтверждает запуск Lua host, observer script и включение Bridge.
Это не проверка запросов или сессии: после критической ошибки запросы не отправлялись.
Текущие LOCAL name/storage/slot не были независимо подтверждены через Bridge.

| Критерий | Результат |
|---|---|
| A — завершённое evidence | UNKNOWN: build оборвался |
| H — полный source/clone HashKey32 evidence | UNKNOWN |
| R — shadow resource readback | UNKNOWN |
| V — visual dependencies | UNKNOWN |
| B — observer session | UNKNOWN |
| C — original integrity | PASS: post-run67/67 |
| writer finalized | FAIL: code2 |
| content DLL unloaded | PASS: свежие state/log |
| реальный render | UNKNOWN |

Evaluator возвращает `LOAD_ONLY_UNCONFIRMED`; операционный blocker —
`BLOCKED_CONTENT_BUILD`. Полный Python suite повторён:691 tests,690 PASS,1 skip,
0 failures,12.433s. Это не устраняет обнаруженную runtime-ошибку.

Автоматический rollback не выполнялся. Исторический preflight dry-run был PASS;
после появления shadow штатный rollback требует отдельной атрибуции/согласования
(`SHADOW_REQUIRES_FRESH_ATTRIBUTION_AND_LINK_AUDIT`). Не заявляется текущая готовность
безусловного отката. Backup и карантины сохранены, неизвестные файлы не удалялись.

Следующий технический шаг — отдельная офлайн-диагностика двух частей graph assert
и их Lua-представления с regression fixture; не ослаблять проверку вслепую.
Текущая задача заканчивается публикацией отчёта. Новая установка, повторный запуск,
spawn или rollback в рамках этого результата не выполняются.

## Runtime checkpoint 2026-11-18 — BLOCKED_CONTENT_BUILD

После сообщения «загрузился» обнаружен Enshrouded PID174844 (ручной запуск
15:35:07 MSK). Копии логов и state сохранены в
`runtime/stage10_10_1_phase_f/20261118T122931689254Z/runtime-capture`.
На критической ошибке дальнейшая runtime-диагностика остановлена.

- Content log сообщает EMF0.6.18, 55 base containers, создание shadow и запуск
  `aic_eml_humanoid 0.5.0` на build1287369.
- Сборка завершилась `AIC_PATCH:graph_changed`, `code=2`.
  State: `built_at=2026-11-18T12:35:08Z`, `unloaded=true`, `truncated=false`;
  fingerprint совпадает с preflight. Пустой массив `errors` не отменяет ненулевой
  code и ошибку в `message`/content.log.
- Assert проверяет одновременно `animationGraph == expected` и `retargetData == nil`.
  Какая часть не выполнена и связано ли это с представлением значений в Lua,
  пока неизвестно. Изменение самих игровых ресурсов этим сообщением не доказано.
- Регистрация clone, финализация writer, evidence v8, visual dependencies и resource
  redirection не подтверждены. Выгрузка content DLL подтверждена логом/state.
  Bridge/observer не вызывались: критическая ошибка обнаружена до этих проверок.
  Текущий LOCAL storage/name/slot через Bridge также не подтверждён.
- `runtime_validation=BLOCKED_CONTENT_BUILD`, `spawn_ready=false`.
  Post-run integrity ожидает ручного закрытия игры. READY_FOR_MANUAL_START ниже —
  исторический preflight, а не текущее состояние.

Код, установленный пакет и receipt не менялись; игровые команды и rollback не
выполнялись. Unit suite повторно не запускался: изменяется только документация.
После «закрыл» проверить originals, installed files и LOCAL относительно baseline,
завершить отчёт и опубликовать результаты в GitHub.

## Checkpoint до ручного запуска, 2026-11-18

**READY_FOR_MANUAL_START**. Phase F явно разрешена пользователем. Runtime тест
ещё не выполнен; итогового load-only verdict пока нет.

Fresh preflight завершён в `2026-11-18T12:29:31.689254+00:00`:

- Build1287369 / Steam26430625 / depot7226436020230696061, Steam idle, game/server закрыты.
- Pinned approved plan/profile/package/binding и настоящий Phase E receipt PASS.
  Installed16/16 SHA/size PASS; clean backup27/27 PASS.
- 137 исходных файлов и23 LOCAL совпали с baseline по SHA/размеру/mtime.
  Полный game inventory153=137+16; конфликтов, неизвестных файлов, reparse points,
  предварительных hardlinks и shadow не обнаружено.
- Сохранён новый snapshot67 оригинальных ресурсов: EXE,KFC,resources,64 DAT,
  с SHA/size/mtime/volume/file ID/link count. Полные153 game/23 LOCAL сохранены отдельно.
- Rollback dry-run по настоящему receipt PASS16; никаких операций отката не выполнено.
  Content input fingerprint совпал с Phase E; это metadata-cache identity,
  а не подтверждение выполненного writer.

LOCAL `default/character0.ksd` и `default/world0.ksd` совпадают с принятым backup
по SHA; в них найдены соответствующие имена Body Test / AI Body Test (по одному
UTF-8 вхождению). Привязка slot1 опирается также на предыдущую runtime-проверку
Stage10.7. Это offline соответствие сохранённых файлов, не декодирование всей
KSD-схемы и не доказательство выбранного сейчас runtime slot. После ручной загрузки
обязательна свежая проверка Bridge character.storage/name/slot и world.name/slot.
Совместимость загрузки прежних saves с новым build пока не установлена; возможные
изменения saves самой игрой будут отдельно зафиксированы, без восстановления.

Private evidence:
`runtime/stage10_10_1_phase_f/20261118T122931689254Z`:
`originals-before.json`, `inventory-before.json`, `rollback-before.json`, `preflight.json`.
[Публичный preflight](../compatibility/migration/1287369/phase_f/preflight.json).
Read-only script: [preflight_phase_f.py](../scripts/preflight_phase_f.py).
Python syntax/compile PASS; реальный preflight exit0. Полный unit suite повторно
не запускался: существующие validators неизменны, новый orchestration script
проверен фактическим read-only выполнением. Исторический691-test результат Phase E
не выдаётся за новый запуск suite.

Следующий checkpoint: пользователь вручную запускает Enshrouded через Steam,
выбирает LOCAL Body Test (slot1) и LOCAL AI Body Test (slot1), сообщает «загрузился».
Codex проверяет только EMF/Bridge/observer/evidencev8, writer/state/shadow/readback/
resource redirection согласно [плану](STAGE10_10_1_LOAD_ONLY_PLAN.md).
При ошибке запуска или отсутствии нужного LOCAL выбора не создавать замену
и не продолжать эксперимент: сохранить сообщение ошибки для диагностики.
Игра закрывается пользователем после runtime capture; затем отдельный post-run audit.

Spawn/despawn, entity/faction/inventory mutations и automatic rollback запрещены.
`runtime_validation=WAITING_FOR_MANUAL_START`, `spawn_ready=false`.
