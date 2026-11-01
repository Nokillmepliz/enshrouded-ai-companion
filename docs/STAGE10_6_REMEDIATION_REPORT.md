# Stage 10.6 — Phase B full rollback/reinstall remediation

Дата: 2026-11-01. Вердикт: **COMPLETE — READY_FOR_PHASE_C_REVIEW**.

## Разрешённая операция

Выполнен полный контролируемый rollback девяти файлов из исходного receipt и повторная установка исправленного plan. Игра и сервер не запускались. Receipt вручную не редактировался, неизвестные файлы не удалялись.

## Проверки перед rollback

- `Enshrouded` и `enshrouded_server`: **NOT_RUNNING**.
- Verified backup `stage10-6-pre-eml-20261101T083034Z`: **PASS**, 24 файла / 224 564 012 байт; backup и текущие source hashes совпали 24/24.
- Исходный receipt: `state=complete`, 9 записей, SHA-256 `d2733c512a51bdaa84787611cbf29597416030e05d9416c4ad0091879a823639`.
- Все 9/9 установленных файлов совпали с исходным receipt.
- Исходный rollback dry-run распознал ровно девять разрешённых путей.

## Rollback

Штатный `rollback_added_files()` удалил только девять файлов из исходного receipt. Выявленный до операции дефект очистки исправлен: installer теперь удаляет известный пустой `mods/aic_eml_humanoid/src` до родительского каталога. Регрессионный тест подтверждает, что посторонний файл в `mods` сохраняется.

После rollback:

- все девять путей отсутствовали;
- исходный receipt сохранился неизменным с тем же SHA-256;
- backup повторно прошёл проверку;
- 55/55 DAT и 22/22 LOCAL save-файла совпали с baseline по SHA-256;
- KFC, KFC resources и EMF loader сохранили закреплённые SHA-256;
- конфликтов и временных `.stage10-install` не обнаружено.

## Новый plan и повторная установка

Повторный preflight подтвердил build `1273043`, verified backup, отсутствие конфликтов и готовность rollback. Созданы отдельные ignored-файлы истории:

- `runtime/stage10_6/install-plan-remediated.json`;
- `runtime/stage10_6/install-receipt-remediated.json`.

Новый receipt имеет `state=complete`, 9 записей и SHA-256 `d8ca5937f03663e7c9e1468890f1126be8e0dcad403bade47384c70d6a1aa15a`. Run token не публикуется; его SHA-256: `30ac223dab85f0fe2a46aaf8e7562c9e4dfcaafd8a8c6eb1b1cc7fbb2461b74d`.

| Файл | SHA-256 |
|---|---|
| `dbghelp.dll` | `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa` |
| `eml.json` | `49d485281fa962f1e5361d9b8982e09400081c0c4c983afb66f493a8c33b5841` |
| `mods/aic_eml_humanoid/mod.json` | `70dc7e989c277c5ddd6f1c544a7387d60b347091f24508ead466c8338f37d91e` |
| `mods/aic_eml_humanoid/README.md` | `bf5fdc8b24718e4522a29187bc7312472f49001153deb8f0a42c9d76162da28b` |
| `mods/aic_eml_humanoid/src/mod.lua` | `f1f7ade2297823414754414f48aac42d23879733dd3268d4aea98f31ac871902` |
| `emf/mods/aic_template_observer/json.lua` | `208334bdd1bdbabc95859c2efdaa07819b1b524c2c991a0aa254d706968f78be` |
| `emf/mods/aic_template_observer/main.lua` | `bdac442e51b111c5bd4774408b52c175935f09f1491b285dd499b43fac99cd53` |
| `emf/mods/aic_template_observer/mod.json` | `423bcb3006f88f3aa207405451a18c3e998d4b9b2974df268e78d8c2d36ce9e8` |
| `emf/config/aic_template_observer.ini` | `a5d6ca2ea3d1a86d4880b224b6bf31ef2b46e6c33d60ce8e3c3105fbf88bec10` |

Исправленный installed README совпадает с repository README и описывает patch 0.3.0/evidence v3. Изменившиеся hashes Lua отражают новый run token.

## Итоговые проверки

- новый receipt и фактические файлы: **9/9 PASS**;
- новый rollback dry-run: **9/9 PASS**;
- verified backup: **24/24 PASS**;
- DAT: **55/55 PASS**;
- LOCAL saves: **22/22 PASS**;
- KFC/resources и EMF loader: **PASS**;
- `Enshrouded` и server после операции: **NOT_RUNNING**;
- полный Python suite: **260 tests run: 259 PASS, 1 skipped**.

Phase B remediation завершена. Phase C ещё не выполнялась и требует отдельного разрешения пользователя. До игрового запуска runtime A/V/B/C остаётся `NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
