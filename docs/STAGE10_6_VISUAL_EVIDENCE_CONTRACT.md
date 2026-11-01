# Stage 10.6 — visual evidence contract v3

Дата: 2026-11-01. Контракт: `aic_eml_humanoid_evidence_v3`.

Контракт предназначен только для load-only проверки EML-клона. Он не разрешает spawn и не доказывает видимую модель сущности.

## Обязательные группы

- Корреляция: `run_token` (32 hex), GUID источника и клона, `npc_id=2939921867`, `faction=PlayerAlly`.
- Структура: полный отсортированный список компонентов и его fingerprint для source/clone.
- `CharacterSetup`: для source и clone экспортируются все 11 полей: `gender`, `voicePackId`, `presetId`, `hair`, `beard`, `hairColorId`, `beardColorId`, `skinColor`, `eyeBrowColor`, `eyeColor`, `useNewProportions`. Каждое поле имеет `status`, `type`, `value`, `provenance`.
- Допустимые статусы: `CONFIRMED`, `MISSING`, `UNKNOWN`, `UNSUPPORTED`. Только `CONFIRMED` с непустыми type/value участвует в совпадении.
- Анимация: source/clone `animationGraph` и `retargetData`. Null retarget является явным значением.
- Visual references: canonical SHA-256 `535732b…d8837`, 18 preset paths и основание сравнения `character_setup_preset_identity`. Полный набор хранится в [hunter_visual_baseline.json](../companion/data/hunter_visual_baseline.json). Он включает ItemInfo, item GUID, RenderModel и gender overrides.
- Целостность: source before/after signature, lookup созданного ресурса, registry status и writer status.
- Provenance: `SOURCE_KFC_VERIFIED`, `CLONE_EML_VERIFIED`, `RESOURCE_EXISTENCE_VERIFIED`, `RUNTIME_RENDER_UNKNOWN`.

`RenderEquipment.lastModels`, runtime handles и `ModelResource` не являются обязательными. Stage 10.5 подтвердил, что визуальная цепочка идёт через `CharacterSetup.presetId → CharacterPresetCollection → ItemInfo → RenderModel → ModelHierarchyResource`.

## Visual fingerprint v2

Уровни строго последовательны:

1. `STRUCTURAL_MATCH`;
2. `CHARACTER_SETUP_MATCH`;
3. `RESOURCE_REFERENCES_MATCH`;
4. `VISUAL_DEPENDENCIES_RESOLVED`;
5. `RUNTIME_RENDER_CONFIRMED`.

Первые четыре могут быть подтверждены load-only evidence. Пятый без созданной и видимой entity остаётся `UNKNOWN`. Пустое значение, отсутствующее поле или неподдержанный тип не повышают уровень. `spawn_ready=false` при любом результате Stage 10.6.

## Acceptance A/V/B/C

- A: identity, faction, source unchanged, run token и внешний факт завершения writer.
- V: структура, все 11 полей, animation/retarget, pinned reference set и resource closure.
- B: меню и LOCAL-мир загружены, критических resource/game errors нет, post-run integrity подтверждена.
- C: EMF, bridge и read-only observer отвечают с тем же token/fingerprint.

`LOAD_ONLY_SUCCESS` возможен только при A=V=B=C=true. Наличие evidence-файла observer трактует как writer-finalized, но evaluator принимает это только с совпадающим token. Observer ограничивает каждую JSON-строку 1023 байтами и сообщает hash/count/status вместо полного reference set.

## Lifecycle и уникальность

`ForceSave` и `ActiveNpcState.npcId` клонируются. Новый npcId вычисляется из отдельного GUID, но уникальность runtime registration до запуска не доказана. Conditional запись в `GuidRegistryResource` повторяет правило исследованного генератора EMF; collision, duplicate unique NPC и writer registration проверяются только в части C. Патч создаёт ресурс, но не entity.
