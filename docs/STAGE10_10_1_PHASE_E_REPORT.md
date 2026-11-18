# Stage 10.10.1 Phase E — установка завершена

2026-11-18. **READY_FOR_PHASE_F_APPROVAL**. Установлены только 16 файлов
согласованного exact-install-manifest. Игра, сервер и скачанные DLL не запускались;
spawn и игровые команды не выполнялись. Phase F требует отдельного согласования.

## Фактические проверки

| Проверка | Результат |
|---|---|
| Игра/server закрыты, Steam idle | PASS перед установкой, между файлами и после |
| Internal build / Steam build / depot | 1287369 / 26430625 / 7226436020230696061 |
| Profile, approved plan, archive, package source hashes | PASS; план и пакет не пересобирались |
| Accepted baseline | CLEAN_BASELINE_PARTIAL, прежнее ограничение принято пользователем |
| Оригинальные файлы до установки | 137/137 hashes и mtime совпали с baseline |
| LOCAL до установки | 23/23, file set/SHA/mtime совпали |
| Verified clean backup | 27/27 до и после установки |
| Конфликты | 16 destinations отсутствовали; неизвестных файлов/links/shadow не обнаружено |
| Установленные файлы | 16/16 SHA-256 и размеры PASS |
| Итоговый inventory | Ровно 137 исходных + 16 установленных файлов |
| Оригиналы после установки | 137/137 SHA/размер/mtime неизменны, включая EXE/KFC/resources и все 64 DAT |
| LOCAL после установки | 23/23 полностью совпадают с baseline |
| Прежние backup/quarantine | Полные inventories до/после совпали, ничего не удалялось |
| Новый receipt | Создан штатным установщиком после проверки16/16; immutable, без ручных правок |
| Rollback dry-run | PASS,16 операций по настоящему receipt; исполнение отката не выполнялось |

Установленные пути и SHA приведены в
[новом install receipt](../compatibility/migration/1287369/phase_e/install-receipt.json).
Все destinations — относительно `D:\SteamLibrary\steamapps\common\Enshrouded`.
Состав: EMF0.6.18 loader/core/content, Lua1.39.0, минимальные configs,
patch0.5.0, observer0.3.0 и deployment binding. Остальные моды не установлены.
Лицензии и bridge-binding остались в project package.

## Идентичность установки и журнал

Approved plan SHA-256:
`82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463`.

Новый install receipt SHA-256:
`c3cd5da70e01fd073553b6dcc2598e8ede867693087b67c285d65253c59d70fc`.

Локальный receipt:
`C:\Enshrouded-ai-companion\runtime\stage10_10_1_phase_e\20261118T122132276076Z\transaction\install-receipt.json`.
Опубликованная metadata-копия receipt имеет тот же SHA. Private run token в неё
не включён; используется связь plan ID / plan SHA / installed hashes.

В той же run-папке сохранены preflight, полный after-inventory, result,
rollback dry-run и transaction journal: immutable intent/verified для каждого
файла. Новый установщик использует exclusive creation, fsync и повторную проверку
source/destination SHA. Нет overwrite, автоматического удаления, восстановления
сохранений, запуска game/server или механизма продолжения частичной установки.
При ошибке сохраняет partial state и останавливается. В реальной установке ошибок
или блокировки защиты не возникло; настройки защиты не менялись.

[Result](../compatibility/migration/1287369/phase_e/result.json),
[rollback dry-run](../compatibility/migration/1287369/phase_e/rollback-dry-run.json).
Существующий clean backup и старые карантины сохранены на прежних местах.

## Тесты и ограничения

Шесть новых installer fixtures PASS: штатная копия/receipt/dry-run, отсутствие
согласия, конфликт, отказ во время записи, изменение source и появление запущенной
игры. Частично записанный fixture сохраняется без ложного completed receipt.
Полный suite: **691 testsRun / 690 PASS / 1 прежний skip**,14.254s,0 failures.
Compileall новых installer/script PASS. Lua и package не менялись; исторический
syntax19/19 не выдаётся за новую проверку. Native код не менялся.

Реальный EMF load, integrated writer, shadow readback, resource redirection,
observer session и визуальное отображение ещё **не проверены**. Не требуется
повторное исследование подтверждённых APIs; нужны наблюдения отдельного load-only
испытания. Текущий metadata input fingerprint сохранён в result, но он не является
доказательством writer completion или заменой SHA-256 файлов.

Следующий шаг: отдельно разрешить Phase F. Перед ручным запуском пользователем
повторить receipt/installed integrity и baseline snapshot, затем выполнить
[контролируемый load-only план](STAGE10_10_1_LOAD_ONLY_PLAN.md) для LOCAL Body Test /
AI Body Test, slot1. До этого игру запускать не предлагается.
После появления runtime shadow rollback потребует свежей attribution/link audit;
нынешний dry-run относится к состоянию до первого запуска.

`installation_authorized=true`, `installation_executed=true`,
`phase_f_authorized=false`, `runtime_status=NOT_EXECUTED`,
`RUNTIME_RENDER_CONFIRMED=UNKNOWN`, **`spawn_ready=false`**.
