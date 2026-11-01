# Stage 10.7 — Phase C controlled load-only report

Дата: 2026-11-01. Итоговый verdict: **LOAD_ONLY_SUCCESS**.

`A/H/R/V/B/C=PASS`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

## Границы испытания

Пользователь вручную запустил Enshrouded, выбрал LOCAL-персонажа `Body Test` (slot 1), загрузил LOCAL-мир `AI Body Test` (slot 1), а затем вручную закрыл игру. Codex не запускал игру и выполнил только read-only диагностику EML/EMF, Python Bridge и observer `status`, `inspect`, `compare`.

Spawn, создание NPC, изменение entity, faction, inventory и игровые команды мутации не выполнялись. Rollback не выполнялся.

## Preflight

- receipt `complete`, SHA-256 `3280870774f3b0283bad0cb6e3063e03ca57f42de8de876578fdf90a269bf2e6`;
- installed hashes: 9/9 PASS;
- verified backup: 24/24 PASS;
- исходные DAT: 55/55 PASS;
- LOCAL baseline: 22 файла;
- rollback dry-run: 9/9 PASS;
- stale runtime outputs и конфликты отсутствовали;
- публичный SHA-256 run token: `53d2a97472f31e0f3501b584d199c826e1ef86e2b42f4c0b3f63f8af921b871f`.

## Runtime evidence v4

EML 0.3.2 применил один patch 0.4.0 и записал marker `AIC_EML_TEMPLATE_V4_READY`. Writer завершился без serialization/fatal errors. Предупреждение о невозможности canonicalize ещё не существовавшего export directory было восстановлено через default path; после него export и evidence успешно создались.

Bridge подтвердил EMF 0.3.2, API 20, protocol 1, build 1273043 и правильный LOCAL-контекст. Observer вернул ровно по одному корректному ответу на `status`, `inspect` и `compare`; JSON, run token и flags `read_only=true`, `spawn_forbidden=true` согласованы. Ошибок observer, resource и game load нет.

Template GUID: `a1c90001-5e4d-4a91-8a1c-000000000001`; source GUID: `e3736dff-0ad2-47fc-903c-66c1775836e8`. Clone содержит 81 компонент, component fingerprint `412d61b0`; lookup fingerprint `a7f38d80`. Read-only lookup через `EML_ASSET_MANAGER_GET_RESOURCE` вернул ожидаемые GUID, `keen::ecs::TemplateResource`, число компонентов и fingerprint. Для `create_resource` отдельная запись в `GuidRegistryResource` не требуется: ресурс находится в EML AppState по composite key.

## HashKey32 source/clone

Метод извлечения: `EML_MAPPED_STRUCT_VALUE_UINT32`. Все значения имеют статус `CONFIRMED`; source provenance — `SOURCE_EML_REFLECTION`, clone provenance — `CLONE_EML_REFLECTION`.

| Поле | Source | Clone |
|---|---:|---:|
| `voicePackId` | 3178345104 | 3178345104 |
| `presetId` | 1602195472 | 1602195472 |
| `hair` | 100818570 | 100818570 |
| `beard` | 0 | 0 |
| `hairColorId` | 2593349132 | 2593349132 |
| `beardColorId` | 2593349132 | 2593349132 |
| `skinColor` | 510686028 | 510686028 |
| `eyeBrowColor` | 1294605571 | 1294605571 |
| `eyeColor` | 1843389514 | 1843389514 |

`gender=Male` и `useNewProportions=false` также совпадают. Unsupported HashKey32 отсутствуют; source до/после чтения не изменён.

## A/H/R/V/B/C

- **A PASS:** format, patch marker, GUID, `npcId=2939921867`, `faction=PlayerAlly`, source identity, token и writer finalized подтверждены.
- **H PASS:** девять HashKey32 имеют корректный тип, UInt32 range, provenance и одинаковые source/clone значения.
- **R PASS:** ресурс создан, writer завершён, lookup доступен и вернул ожидаемую identity.
- **V PASS:** совпадают 81-компонентная структура, `CharacterSetup`, animation graph `402df515-5965-4b01-a17b-17d482a91af4`, visual references и dependencies.
- **B PASS:** нужный LOCAL-мир загрузился, resource/game errors отсутствуют, post-run source integrity подтверждена.
- **C PASS:** Bridge/observer доступны; ответы полны, read-only и запрещают spawn.

## Post-run integrity

- Enshrouded и server после закрытия: NOT_RUNNING.
- Verified backup: 24/24 PASS; install files: 9/9 PASS.
- Исходные DAT `000–054`: 55/55 SHA-256 PASS. Добавлены только ожидаемые пустые DAT `055–063` с SHA-256 `e3b0c442…b855`; удалённых и изменённых исходных DAT нет.
- EML изменил `enshrouded.kfc` с baseline `54a8cb76…00a92` на `f5e19208…9a58d`; `enshrouded.kfc.bak` точно совпадает с baseline.
- `enshrouded.kfc_resources` изменён с `53786c45…7cb3d` на `45e2f590…3568`; baseline сохранён в verified backup.
- LOCAL-набор сохранил 22 файла, added/removed 0. Штатно изменились 7 файлов текущего character/world и ротационных backup: `character0.ksd`, `world0.ksd`, две character backup и три world backup.
- Неизвестных изменений: 0. Rollback readiness: true. Rollback executed: false.

## Практический предел результата

Load-only тест подтвердил сериализацию и повторный lookup template, точное копирование `CharacterSetup`, animation graph и доступность visual dependencies. Он не подтверждает фактический runtime render: независимая entity не создавалась, поэтому модель, материалы, skeleton, анимация, initial faction, ownership, поведение и безопасный dismiss на экране остаются неизвестными.

Нужен отдельный этап и отдельное разрешение пользователя для проектирования ограниченного spawn-теста. До этого `spawn_ready=false`.
