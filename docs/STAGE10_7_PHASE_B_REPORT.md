# Stage 10.7 Phase B — controlled rollback/reinstall report

Дата: 2026-11-01. Статус: **COMPLETE — READY_FOR_PHASE_C_REVIEW**. Enshrouded и dedicated server не запускались; spawn/entity/faction/inventory actions не выполнялись. LOCAL-сохранения не восстанавливались и не изменялись операциями Phase B.

## Pre-rollback audit

- Игра/server закрыты.
- Старый receipt 0.3.0: `complete`, SHA-256 `d8ca5937f03663e7c9e1468890f1126be8e0dcad403bade47384c70d6a1aa15a`; 9/9 installed hashes совпали.
- Verified backup Stage 10.6: 24/24 PASS.
- DAT 000–054: 55/55 baseline hashes PASS. DAT 055–063: ровно девять атрибутированных EML-файлов нулевой длины.
- `enshrouded.kfc.bak` совпал с исходным KFC baseline. Текущие KFC/resources отличались от baseline и были ранее атрибутированы EML.
- LOCAL: 22 файла, набор неизменен; относительно pre-Stage10.6 baseline изменены шесть ожидаемых файлов `character0.ksd`, `world0.ksd` и по две их backup-копии. Added/removed: 0. Unknown changes: 0.

## Rollback и чистое состояние

Штатный rollback удалил ровно 9 путей старого receipt. `restore_game_data` восстановил только `enshrouded.kfc` и `enshrouded.kfc_resources`, удалил проверенный `.bak` и DAT 055–063. Удалены только атрибутированные EML runtime directories `.cache`, `export`, `logs`.

После отката:

- KFC SHA-256: `54a8cb76b3229c486ef55a7ababcd48828fa0ffc5bb144d206f687fd0ab00a92`;
- KFC resources SHA-256: `53786c45797d275661f3ccc1fd8c84527a74f376e01f05fc76351f91fb17cb3d`;
- DAT: ровно 000–054, 55 файлов;
- старые 9 install paths отсутствуют;
- неизвестных изменений нет;
- LOCAL hashes до/после rollback совпали.

## Новый backup и установка

Создан новый backup текущего LOCAL-состояния `runtime/backups/stage10-7-pre-eml-20261101`: 24 файла, 224 564 012 байт, verification 24/24; manifest SHA-256 `7ac4df3609d2609673345d029844dcf8d9181ba768762aa6eb6b62752cb9b651`.

Новый install plan содержит ровно 9 файлов. Receipt: `complete`, SHA-256 `3280870774f3b0283bad0cb6e3063e03ca57f42de8de876578fdf90a269bf2e6`. Новый run token внедрён ровно в patch и observer; публикуется только его SHA-256: `53d2a97472f31e0f3501b584d199c826e1ef86e2b42f4c0b3f63f8af921b871f`.

| Installed path | SHA-256 |
|---|---|
| `dbghelp.dll` | `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa` |
| `eml.json` | `49d485281fa962f1e5361d9b8982e09400081c0c4c983afb66f493a8c33b5841` |
| `mods/aic_eml_humanoid/mod.json` | `3a9c91f94e708505960835e43ccc01ba9b07948ee3e7f9101ba194d045a18237` |
| `mods/aic_eml_humanoid/README.md` | `a9200a897c17e97ace23e89d7a11dd2008479f78549f2bdbf3f0f7bce060c0e0` |
| `mods/aic_eml_humanoid/src/mod.lua` | `25ab14dea350cce05d1e6d6c7e76e169e342fc65893330b5f1f963e20aa395d4` |
| `emf/mods/aic_template_observer/json.lua` | `208334bdd1bdbabc95859c2efdaa07819b1b524c2c991a0aa254d706968f78be` |
| `emf/mods/aic_template_observer/main.lua` | `594308c75d6b2a0f8e6ec2082aee74d0a50a37ec8c54b705b10f3802b54c1535` |
| `emf/mods/aic_template_observer/mod.json` | `423bcb3006f88f3aa207405451a18c3e998d4b9b2974df268e78d8c2d36ce9e8` |
| `emf/config/aic_template_observer.ini` | `a5d6ca2ea3d1a86d4880b224b6bf31ef2b46e6c33d60ce8e3c3105fbf88bec10` |

Независимая post-install verification подтвердила 9/9 receipt hashes, patch `0.4.0`, evidence v4, v4-compatible read-only observer, отсутствие placeholder, совпадение токена, backup и его 24 текущих sources, отсутствие pre-runtime `.cache/export/logs/.bak`, DAT 55/55 и rollback dry-run 9/9. LOCAL hashes совпадают с новым backup.

## Ограничения

Phase C не выполнялась. Patch 0.4.0 ещё не загружался EML, evidence v4 не создавался, A/H/R/V/B/C не оценивались. `spawn_ready=false`. Следующий шаг требует отдельного разрешения на ручной load-only тест; игру запускает пользователь.
