# Stage10.10.1 — ограниченная Phase B выполнена

2026-11-18. Основание: отдельное разрешение пользователя на backup около420MB и карантин **только81** записанного в reviewed manifest файла; остальные51 оставить. Неполный backup принят пользователем. Phase C, Steam Verify, игра/server, новые модификации и старый rollback не разрешались и не выполнялись.

Вердикт: **LIMITED_PHASE_B_COMPLETED**. `clean_baseline_confirmed=false`, `installation_ready=false`, `phase_c_executed=false`, `runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`. `cleanup_executed=true` относится исключительно к разрешённым81 файлам, не к полной очистке или восстановлению ресурсов.

## Пути и фиксация scope

| Объект | Путь |
|---|---|
| Игра | `D:\SteamLibrary\steamapps\common\Enshrouded` |
| LOCAL | `C:\Users\user\Saved Games\keen games\Enshrouded` |
| Backup | `C:\Enshrouded-ai-companion\runtime\backups\stage10-10-1-phase-b-20261118T1035Z` |
| Карантин | `C:\Enshrouded-ai-companion\runtime\quarantine\stage10-10-1-phase-b-20261118T1035Z` |
| Raw before/after inventory | `C:\Enshrouded-ai-companion\runtime\stage10_10_1_phase_b\20261118T1035Z` |
| Публичные результаты | [operation.json](../compatibility/recovery/1287369/phase_b/operation.json), [residual-review.json](../compatibility/recovery/1287369/phase_b/residual-review.json) |

Reviewed commit: `21d7860ac8b399d570fe37df0f2478bad6102547`. [Исходный manifest](../compatibility/recovery/1287369/cleanup_manifest.json) побайтно совпал с ним и не редактировался. Raw SHA256: `2d699685c12cb39edc69e924c6a887b4f22dacb218f10ab271713610e3097e4d`.

Preflight: game/server отсутствовали; version1287369, Steam build26430625/depot manifest7226436020230696061 соответствуют плану. Fresh249 game/23 LOCAL совпали с Phase A по SHA/size/mtime; новых файлов нет. Steam manifest показывал StateFlags4 и завершённые download/stage counters; это локальное наблюдение, Steam не управлялся через Codex.

## Проверенный backup

Штатный `stage10_10_1_recovery.py backup --execute --authorization PHASE_B_BACKUP` выполнил preflight, copy и reread каждого файла. Затем отдельно выполнен `verify-backup`, а после карантина — ещё одна независимая проверка через post-audit.

- 208 non-DAT игровых/LOCAL файлов + приватный install receipt = **209/209 payload files** с совпавшими SHA-256/size.
- Payload: **419971833 bytes**. С `plan.json` и `manifest.json`: **211 файлов,420406619 bytes**.
- Все64 DAT представлены хешами в сохранённом plan.json; тела DAT не копировались. Полный возврат mixed state после Steam Verify не гарантируется, `full_mixed_state_restore=false`.
- Backup manifest SHA256: `67a542553c82328bcdd589a1f4067c034bf0315fa8e375dd5a89b341c177333b`.
- Backup plan SHA совпадает с reviewed manifest. Исторический receipt в проекте остался неизменным; его приватное содержимое не публикуется.

## Карантин и post-inventory

Использован тот же штатный CLI, `quarantine --execute --authorization PHASE_B_QUARANTINE`, с explicit reviewed plan SHA и verified backup. Перед unlink каждого файла проверялись game/server, build/Steam/receipt, исходный hash, backup copy и quarantine copy. Директории целиком не удалялись. API/ручное исправление старого receipt или старый rollback не применялись.

| Проверка | Результат |
|---|---|
| Разрешённые перемещения | **81/81**,29 504 495 bytes |
| Полнота копий карантина | **81/81 SHA/size PASS**, посторонних payload files нет |
| Журнал |162 records:81 COPIED_VERIFIED_SOURCE_PRESENT +81 QUARANTINED, точная последовательность manifest |
| Остаток игры |249 →168 файлов; ровно81 разрешённый путь отсутствует |
| Остальные игровые файлы |**168/168 unchanged**, включая size/SHA/mtime |
| MANUAL_REVIEW |**51/51 unchanged** |
| DAT |**64/64 unchanged**, включая055–063 |
| EXE/KFC/resources/KFC.bak |Неизменны |
| LOCAL |**23/23 unchanged**, без added/removed/changed |
| Старые известные loaders |dinput8.dll, dbghelp.dll, emf/emf_core.dll отсутствуют в исходных путях |
| Root DLL после карантина |Только3 проверенных NVIDIA/Valve components |
| Game/server после операции |0 процессов |

Карантин содержит81 payload + `journal.jsonl`; не очищался. Journal SHA256: `27a3a7b79a590e692c14584d1106a3a4f20112e2f26cad005a32abb1e52237d9`. Эти файлы сохраняются для будущего отдельно рассмотренного восстановления; автоматический restore не выполнялся.

## Проверка оставшихся51

[Подробный разбор](STAGE10_10_1_RESIDUAL_FILES_REVIEW.md) классифицирует каждый файл, не меняя исходный action.

Главные препятствия clean baseline: current KFC64 containers против `.bak`55 при одинаковой версии; недоказанное происхождение `.bak` и DAT055–063; ранее установленный clone в hash-неизменившейся resource database. Integrated `choose_base` при нынешнем заголовке выбрал бы `.bak`, поэтому ей нельзя доверять автоматически.

Отдельные препятствия безопасной миграции:23 old configs, legacy body.lua, installer catalog,4 cache-файла и старый exportv4. Обнаружено exact совпадение body.lua с commit026cd8a; aic_body и Lua configs сохраняют enabled1. Сейчас старое тело не имеет main/mod.json/loader и не запускается; будущая установка должна исключить слепое наследование этих остатков.

Три vendor DLL имеют Authenticode Valid: две NVIDIA и Valve Steam API. Их нельзя считать модами только по расширению DLL; соответствие depot ещё не доказано. Settings JSON и исторические diagnostics не являются основанием для дополнительного удаления. Все51 оставлены на месте, как разрешено пользователем.

## Проверки кода и публикация

Добавлен read-only [post-audit helper](../scripts/stage10_10_1_phase_b_audit.py): exact before/after scope, immutable reviewed plan, backup verification,81 quarantine hashes/162 journal records, fresh residual inspection и sanitized output. Он не вызывает cleanup/install/game/Bridge. [11 новых тестов](../tests/test_phase_b_audit.py) проверяют подмену удалённого файла при том же count, дополнительные/изменённые файлы, timestamp-only и LOCAL changes, before/plan mismatch, missing removal и KFC header bounds.

Полный Python suite: **597 testsRun /596 PASS /1 skipped /0 failures**; новые11 PASS, recovery/migration61 PASS. Один skip — историческая Windows directory-symlink privilege проверка; junction test проходит. `compileall` и diff check PASS. Lua/Rust/C++ не изменялись; прошлые результаты не выдаются за повторный запуск.

В GitHub публикуются этот отчёт, разбор51 файлов, sanitized metadata, helper/tests и PROGRESS. Backup/quarantine payload, приватные receipts/tokens, Steam account metadata и игровые/LOCAL данные остаются только в ignored runtime.

EMF integrated content **принят пользователем как будущая архитектура**, при условии подтверждения целостности оригиналов и корректности shadow resources. Сейчас не установлен. Следующий шаг — отдельное согласование Phase C; никакой Steam Verify, дополнительной очистки, установки или запуска игры из этого отчёта не следует. Работа остановлена.
