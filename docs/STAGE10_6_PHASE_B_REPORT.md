# Stage 10.6 — Phase B installation report

Дата: 2026-11-01. Итоговый вердикт после remediation: **COMPLETE — READY_FOR_PHASE_C_REVIEW**.

## Preflight

- `Enshrouded` и `enshrouded_server` отсутствовали до backup, непосредственно перед установкой и после неё.
- Build: `1273043`.
- SHA-256 `enshrouded.exe`: `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882`.
- SHA-256 `enshrouded.kfc`: `54a8cb76b3229c486ef55a7ababcd48828fa0ffc5bb144d206f687fd0ab00a92`.
- SHA-256 `enshrouded.kfc_resources`: `53786c45797d275661f3ccc1fd8c84527a74f376e01f05fc76351f91fb17cb3d`.
- SHA-256 EMF `dinput8.dll`: `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee`.
- SHA-256 EML `dbghelp.dll`: `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa`.
- Конфликты `dbghelp.dll`, `eml.json`, EML patch, observer, config, stale export и `enshrouded.kfc.bak` отсутствовали.
- Dry-run plan содержал ровно девять разрешённых файлов.

## Verified backup

Создан новый backup `stage10-6-pre-eml-20261101T083034Z`: **24 файла, 224 564 012 байт**. В него вошли два KFC-файла и 22 файла LOCAL-профиля `default`.

Проверки:

- 24/24 backup hashes совпали с manifest;
- 24/24 текущих source hashes после копирования совпали с manifest;
- исходные EXE/KFC/resources/EMF/EML hashes не изменились;
- post-backup preflight подтвердил `installation_ready=true` и `rollback_ready=true`.

Backup, manifest и LOCAL-сохранения находятся только в ignored `runtime`; в Git они не публикуются.

## Установленные файлы

| Файл | SHA-256 |
|---|---|
| `dbghelp.dll` | `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa` |
| `eml.json` | `49d485281fa962f1e5361d9b8982e09400081c0c4c983afb66f493a8c33b5841` |
| `mods/aic_eml_humanoid/mod.json` | `70dc7e989c277c5ddd6f1c544a7387d60b347091f24508ead466c8338f37d91e` |
| `mods/aic_eml_humanoid/README.md` | `3a2a12ac7adb67e4e8981d615596842dada06f050f3d6542d7cae39aa9db7b1b` |
| `mods/aic_eml_humanoid/src/mod.lua` | `e8bec2a0427e8919552ede5148f2682ceb2d913514588bb18ef139cac0850a91` |
| `emf/mods/aic_template_observer/json.lua` | `208334bdd1bdbabc95859c2efdaa07819b1b524c2c991a0aa254d706968f78be` |
| `emf/mods/aic_template_observer/main.lua` | `d80f71a8fe3c081e721e789fd52c2a1efcb212e06d846bbc62b98c17f150a8d8` |
| `emf/mods/aic_template_observer/mod.json` | `423bcb3006f88f3aa207405451a18c3e998d4b9b2974df268e78d8c2d36ce9e8` |
| `emf/config/aic_template_observer.ini` | `a5d6ca2ea3d1a86d4880b224b6bf31ef2b46e6c33d60ce8e3c3105fbf88bec10` |

Receipt имеет `state=complete`, `patch_version=0.3.0`, build `1273043` и 9 записей. Новый run token имеет 128 бит; в Git записан только его SHA-256: `12161c78d96705d70edba23e1cb139b05adbc96ac40aa33155b891f3ae413a`. Placeholder отсутствует в установленных Lua-файлах, token присутствует в каждом ровно один раз.

## Post-install и rollback

- Все 9/9 фактических hashes совпали с receipt.
- KFC и 22 LOCAL save-файла после установки совпали с verified backup; установка их не меняла.
- Baseline содержит 55 DAT и 22 LOCAL save-файла для будущей post-run сверки.
- Временные `.stage10-install` отсутствуют.
- Rollback dry-run подтвердил все девять удаляемых файлов; неизвестных состояний нет.
- `WinDefend` и `SecurityHealthService` работают. Защита не отключалась и её настройки не менялись.

## Runtime status

Игра не запускалась, EML не загружался, evidence v3 ещё не создан. Уровни A/V/B/C — **NOT_EXECUTED**, `load_only_success=false`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

## Обнаруженное расхождение и остановка

После успешной hash-сверки выполнена дополнительная содержательная проверка. Установленные `mod.json` и `src/mod.lua` действительно относятся к patch 0.3.0/evidence v3, однако включённый в тот же plan `README.md` содержит устаревшее описание patch 0.2.0 и утверждение «не установлен». Это не влияет на исполняемый Lua, но противоречит фактическому дистрибутиву.

Согласно условию пользователя «при любых несовпадениях остановиться», установочные действия прекращены. Игровой README и complete receipt не изменялись после обнаружения. В репозитории README исправлен, а offline validator усилен, чтобы stale README блокировал будущий plan. Для приведения установленной копии к исправленному plan требуется отдельное разрешение; до этого Phase C **BLOCKED**.

Разрешённая попытка remediation остановлена без изменений: штатный installer не поддерживает revision существующего receipt и fail-closed возвращает `installation_collision:dbghelp.dll`. Полный аудит: [STAGE10_6_REMEDIATION_REPORT.md](STAGE10_6_REMEDIATION_REPORT.md).

## Full rollback/reinstall remediation

После отдельного разрешения выполнен штатный rollback всех девяти файлов исходного receipt и повторная установка исправленного plan. Исходный receipt сохранён неизменным как история; новый complete receipt создан отдельно. Исправленный README 0.3.0 установлен, фактические hashes совпали 9/9, новый rollback dry-run прошёл 9/9.

После rollback и после повторной установки verified backup прошёл проверку 24/24; 55 DAT и 22 LOCAL save-файла совпали с baseline по SHA-256. Игра/server не запускались, NPC не создавался. Полный итог: [STAGE10_6_REMEDIATION_REPORT.md](STAGE10_6_REMEDIATION_REPORT.md).

Phase B завершена. Phase C готова только к отдельному рассмотрению и всё ещё требует явного разрешения пользователя. Spawn и любые команды мутации запрещены.
