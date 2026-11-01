# Stage 10.6 — Phase C controlled load-only report

Дата: 2026-11-01. Итоговый verdict: **FAILED — V:CHARACTER_SETUP**.

`load_only_success=false`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

## Границы испытания

Пользователь вручную запустил Enshrouded и загрузил LOCAL-персонажа `Body Test`, slot 1, в LOCAL-мир `AI Body Test`, slot 1. Codex выполнил только read-only операции EMF Bridge и observer `status`, `inspect`, `compare`, затем прочитал журналы и evidence v3. Spawn, faction, inventory, entity и save-команды не выполнялись. Игру закрыл пользователь. Rollback не выполнялся.

## Preflight

- новый install receipt: `state=complete`, 9 записей, SHA-256 `d8ca5937f03663e7c9e1468890f1126be8e0dcad403bade47384c70d6a1aa15a`;
- фактические install hashes: 9/9 PASS;
- verified backup: 24/24 PASS;
- baseline: 55 DAT и 22 LOCAL save-файла;
- stale evidence, KFC `.bak`, EML cache/export/logs, bridge descriptor и install temporary отсутствовали;
- конфликты не обнаружены.

## Runtime evidence

EML 0.3.2 запустил `aic_eml_humanoid`, сформировал `aic_eml_humanoid_evidence_v3` размером 8 887 байт и сообщил `Applied 1 patches`. Повторный EML pass сообщил `No changes detected, skipping patching`.

Bridge подтвердил EMF 0.3.2, API 20, protocol 1, build 1273043 и правильный LOCAL-профиль. Observer вернул все три ответа без protocol/JSON/token errors. Его ответы имели `read_only=true`, `spawn_forbidden=true` и совпадающий run token/fingerprint `53d4d5da`.

## A/V/B/C

| Уровень | Результат | Доказательство |
|---|---|---|
| A — EML patch | **PASS** | format/token, clone/source GUID, `npcId=2939921867`, `faction=PlayerAlly`, source unchanged и writer finalized подтверждены. |
| V — visual clone | **FAIL** | Structure, references, dependencies, animation и retarget прошли; строгий typed `CharacterSetup` не прошёл. |
| B — game/integrity | **PASS** | Главное меню и правильный LOCAL-мир загружены; post-run integrity не обнаружила неизвестных изменений. |
| C — EMF runtime | **PASS** | Bridge и observer доступны; token и fingerprint коррелированы, все observer safety flags подтверждены. |

## Что подтверждено визуально

- Структура clone совпадает с source: 81 компонент, component fingerprint `412d61b0`. В набор входят `CharacterSetup`, `RenderEquipment`, `AnimationGraphResourceComponent2`, `ForceSave` и `ActiveNpcState`.
- `gender=Male` и `useNewProportions=false` подтверждены typed evidence и совпадают у source/clone.
- Animation graph source/clone совпадает: `402df515-5965-4b01-a17b-17d482a91af4`.
- Retarget source/clone совпадает: null GUID `00000000-0000-0000-0000-000000000000`.
- EML evidence сообщает совпадение canonical reference set из 18 записей, SHA-256 `535732bda93e41ff3b3070e362d649b9c6875101826d2c1823c81945b22d8837`, и `visual_dependencies_resolved=true`.
- Source signature до/после совпала: `source_unchanged=true`.

Эти результаты подтверждают структурное клонирование и связь с исследованной visual dependency closure. Они не доказывают фактический render модели, поскольку entity не создавалась.

## Причина отказа V

Девять полей `CharacterSetup` типа `HashKey32` имеют одинаковый статус у source/clone, но EML экспортировал их как `UNSUPPORTED` с пустым value:

- `voicePackId`;
- `presetId`;
- `hair`;
- `beard`;
- `hairColorId`;
- `beardColorId`;
- `skinColor`;
- `eyeBrowColor`;
- `eyeColor`.

По контракту v3 совпадение допускается только при `CONFIRMED` и непустых typed values. Поэтому общий marker `character_setup_match=true` и observer `compare.ok=true` не заменяют строгую проверку; evaluator правильно вернул `V:character_setup`.

## Регистрация шаблона

Patch создал сериализованный template evidence с новым GUID, и observer увидел clone evidence. Однако `source_registered=false` и `registry_added=false`; прямой EMF lookup остаётся `UNAVAILABLE_WITHOUT_ENTITY`. Регистрация нового GUID в `GuidRegistryResource` и runtime-доступность template через независимый lookup **не подтверждены**. Collision не наблюдался, но без независимой регистрации это не считается полным acceptance.

## Журналы

EML один раз предупредил, что не смог canonicalize отсутствующий export directory и использовал default; после этого export и evidence успешно созданы. В игровом журнале повторился известный по предыдущему Stage 10.2 diagnostic `Could not find component ... when loading template Benchmark`; игра продолжила загрузку, и он не коррелирует с новым template GUID. Критических EML/resource ошибок нового patch не найдено.

## Post-run integrity

- Enshrouded/server после закрытия: NOT_RUNNING.
- Backup: 24/24 PASS.
- Install files: 9/9 совпадают с новым receipt.
- Исходные DAT `000–054`: 55/55 SHA-256 PASS.
- Добавлены только ожидаемые нулевые DAT `055–063`, SHA-256 пустого файла у каждого `e3b0c442…b855`.
- EML изменил KFC на `b1c15176…7babf`; `enshrouded.kfc.bak` точно совпадает с baseline `54a8cb76…0a92`.
- KFC resources изменён EML на `45e2f590…3568`; baseline сохранён в verified backup.
- LOCAL-набор сохранил 22 файла: добавленных/удалённых нет, штатно изменились 6 файлов текущего character/world и их ротационных backup.
- Неизвестные изменения: 0. Rollback readiness: true. Rollback executed: false.

## Оставшиеся неизвестные

- typed значения девяти `HashKey32` полей;
- независимая runtime-регистрация и lookup нового template;
- фактическая созданная entity, её модель, материалы, skeleton и анимация на экране;
- `RUNTIME_RENDER_CONFIRMED` остаётся `UNKNOWN`;
- spawn остаётся запрещённым и `spawn_ready=false`.

Следующий технический этап должен исследовать поддержку чтения `HashKey32` в EML Lua binding и способ независимой проверки регистрации без создания entity. Он требует отдельного задания и не является разрешением на spawn или rollback.
