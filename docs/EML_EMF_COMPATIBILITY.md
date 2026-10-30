# Совместимость EML 0.2.0 и EMF 0.3.2

Дата офлайн-проверки: 2026-10-31. Игра не запускалась, EML не устанавливался, KFC и сохранения не изменялись.

## Версии и происхождение

| Компонент | Версия / идентификатор | Доказательство |
|---|---|---|
| Enshrouded | build `1273043` | SHA-256 `enshrouded.exe` `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882`; установленный EMF ранее записал `known build 1273043` |
| EMF | 0.3.2, API 20 | установленный `dinput8.dll` SHA-256 `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee`; pinned source [`08d60015`](https://github.com/matenm/emf-enshrouded/tree/08d600155fcadc8e45cc9c6f3932a67c717345be) |
| Lua host | 1.9.0 | предыдущий игровой журнал EMF и manifest observer `depends.lua >=1.9` |
| EML | 0.2.0 | официальный [GitHub Release v0.2.0](https://github.com/Brabb3l/kfc-parser/releases/tag/v0.2.0), tag/commit [`16708594`](https://github.com/Brabb3l/kfc-parser/tree/16708594d686b030d909f2d835b199d879ea9ad8) |

GitHub API публикует release assets:

| Файл | Размер | SHA-256 GitHub и локальный | Назначение |
|---|---:|---|---|
| `dbghelp.dll` | 20 614 895 | `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa` | рекомендуемый EML proxy; единственный loader, нужный эксперименту |
| `emm.exe` | 21 325 000 | `b1133f6b8ea7000596cc7710901bd8307b48165b0e650c0487a611d90ea49305` | CLI; для proxy-эксперимента не устанавливается |
| `dinput8.dll` | 20 576 572 | `1ff5334c46ab635ab7602701e2d63f32447bc4b258e942d85b2c0273b8457e2e` | альтернативный EML proxy; **не использовать**, имя занято EMF |

`dbghelp.dll` и `emm.exe` скачаны только в ignored `runtime/stage10/downloads`, побайтно совпали с GitHub digests и не запускались. Оба PE32+ x64 (`machine 0x8664`, `magic 0x20b`), Authenticode `NotSigned`. GitHub artifact attestation для digest не найдена (API 404). Microsoft Defender просканировал оба файла без детектов; защита не отключалась. Это подтверждает происхождение конкретных bytes, но не доказывает их безопасность или воспроизводимую идентичность исходникам.

Статические imports ограничены Windows/API-set DLL: `KERNEL32`, `ntdll`, `user32`, `userenv`, `ws2_32`, `bcryptprimitives`, `oleaut32` и Universal CRT API sets. Соседних third-party DLL не требуется. В бинарниках присутствуют build paths `D:\a\kfc-parser\kfc-parser\crates\...`, совпадающие со структурой официального workflow; `emm.exe` содержит версию `0.2.0`. Workflow tag использует Rust 1.88.0, target `x86_64-pc-windows-gnu`, `cargo build --locked` и tests для CLI. Локального Rust toolchain нет, поэтому независимая пересборка не выполнялась.

## DLL и порядок загрузки

EMF установлен как `dinput8.dll`. EML официально рекомендует `dbghelp.dll`; в текущем каталоге игры `dbghelp.dll`, `eml.json`, корневой `mods` и `enshrouded.kfc.bak` отсутствуют. Имена proxy не конфликтуют. EML-вариант `dinput8.dll` запрещён preflight как несовместимый с установленным EMF.

Windows загружает оба proxy по импорту игры; точный взаимный порядок их инициализации не документирован. EML patch должен закончить изменение KFC до чтения asset database игрой, EMF и Lua host активируются позже на runtime. EML не заявляет Vulkan hook; он проксирует `dbghelp` и работает с KFC. EMF отдельно использует Vulkan overlay. Отсутствие прямого hook-конфликта следует из архитектуры, но совместная загрузка двух конкретных DLL остаётся `UNKNOWN` до фазы B.

## Матрица совместимости

| Проверка | Статус | Доказательство / предел |
|---|---|---|
| EML отдельно | `OFFLINE_READY`, runtime `UNKNOWN` | официальный asset, hash/signature/PE/import/Defender audit; бинарник не запускался |
| EMF отдельно | `CONFIRMED_PREVIOUSLY` | предыдущий игровой журнал: EMF 0.3.2, build 1273043, API 20, Lua и bridge |
| EML + EMF | `UNKNOWN` | разные proxy names, но совместный process start ещё не выполнялся |
| Vulkan | `LIKELY_NO_DIRECT_CONFLICT` | EML source не устанавливает Vulkan overlay; runtime не проверен |
| Python Bridge после EML | `UNKNOWN` | EML не меняет bridge API; соединение после совместного старта не проверено |
| Новый TemplateResource | `OFFLINE_VALIDATED`, runtime `UNKNOWN` | настоящий `create_resource`, fixed GUID, повторный lookup и EML evidence; writer/game load не выполнялись |
| Прямой lookup template через EMF Lua | `UNSUPPORTED_WITHOUT_ENTITY` | публичный `world:template(component, entity)` требует entity; API перечисления/lookup GUID нет |

Последнее ограничение существенно: при запрете spawn EMF Lua не может независимо получить новый `TemplateResource` по GUID. Публичный контракт описывает только [`world:template(component, id)`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L169), а [реализация binding](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/lua_host/bindings.cpp#L225-L248) принимает entity ID. API перечисления или lookup `TemplateResource` по GUID в публичном Lua surface не найден. `aic_template_observer` читает положительный export EML и честно возвращает `direct_emf_template_lookup=UNAVAILABLE_WITHOUT_ENTITY`. Это доказывает загрузку observer и доступ к evidence, но не прямой lookup ресурса через EMF.

## Критерий этапа 10.1

Прямой lookup остаётся отдельной неподтверждённой capability. Он больше не блокирует узкий результат `LOAD_ONLY_SUCCESS`. Для него нужны три независимых результата: EML создал и writer записал resource; игра загрузила изменённую asset database и тестовый LOCAL-мир без ошибок; EMF/Lua/observer/Python Bridge работают в том же процессе. Ни один из этих результатов не выдаётся за прямое чтение нового GUID через EMF.

Один запуск связывает случайный `run_token`: install receipt → установленный EML patch → evidence/EML marker → установленный observer → EMF marker/ответы → bridge/game/integrity reports. Совпадение timestamp без токена недостаточно. Формальные правила приведены в [STAGE10_1_ACCEPTANCE_CRITERIA.md](STAGE10_1_ACCEPTANCE_CRITERIA.md).

## EML mod discovery и изменения данных

Согласно [официальной инструкции EML](https://brabb3l.github.io/kfc-parser/eml/usage.html), proxy ищет `<game>\mods\<id>\mod.json` и `src\mod.lua`; конфигурация находится в `<game>\eml.json`. Для evidence требуется `use_export_flag=true`, output — `<game>\export\aic_eml_humanoid\template_evidence_v1.txt`.

Исходники [`mod-loader-lua`](https://github.com/Brabb3l/kfc-parser/tree/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua) подтверждают:

- backup `enshrouded.kfc` в `enshrouded.kfc.bak`;
- rewrite `enshrouded.kfc`;
- append изменённых/new resources в `enshrouded.kfc_resources`;
- возможное создание новых `enshrouded_NNN.dat` для content;
- type/cache files и file-state cache;
- повторный patch после изменения game/mod files, иначе cache может пропустить неизменившийся run.

Наш patch создаёт resource, но не вызывает `create_content`; новые DAT не ожидаются как обязательный результат. Rollback всё равно считает любой новый DAT отдельным изменением и требует явного review.

## Положительные сигналы будущего запуска

Успех EML-части требует одновременно:

1. свежий evidence-файл с `resource_lookup_after_create=true`, правильными GUID/npcId/faction/model/animation/components и `source_unchanged=true`;
2. строку `AIC_EML_TEMPLATE_READY <GUID> 2939921867 ...` в журнале того же запуска;
3. последующую строку `Applied N patches`, где `N > 0`, подтверждающую writer finalization;
4. отсутствие serialization/resource collision errors;
5. успешный запуск EMF/Lua/bridge и ответы observer.

Отсутствие ошибок само по себе успехом не считается.
