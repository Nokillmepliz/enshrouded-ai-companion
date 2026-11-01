# Этап 10.5 — visual dependencies Humanoid NPC

Статус: **source chain confirmed from KFC; clone/runtime remain UNKNOWN**.

## Template comparison

Оба template успешно декодированы как `keen::ecs::TemplateResource`, имеют по 81 component и одинаковый набор component types. В обоих присутствуют `CharacterSetup`, `NewCharacterSetup`, `EquipmentCheck`, `InventorySetup`, `RenderEquipment` и `AnimationGraphResourceComponent2`.

| Поле | hunter_assistant | blacksmith_assistant |
|---|---|---|
| presetId | `1602195472` | `4189673484` |
| gender | `Male` | `Female` |
| hair | `100818570` | `742677050` |
| voicePackId | `3178345104` | `1773411200` |
| animationGraph | `402df515-5965-4b01-a17b-17d482a91af4` | тот же GUID |
| retargetData | `null` | `null` |
| RenderEquipment.lastModels | 24 × `null` | 24 × `null` |
| Inventory slots / links | пустые / zero runtime IDs | пустые / zero runtime IDs |

Значения `CharacterSetup` являются HashKey32/enum и не интерпретируются как GUID. Их target presets найдены по точному `presetId` в `keen::CharacterPresetCollection`.

## Preset → ItemInfo → RenderModel

`CharacterPresetCollection` содержит 54 presets и прямые GUID references. `ItemRegistryResource` содержит 4207 синхронных пар `itemRefs/dbgNames`. Для двух target presets извлечены 24 уникальных `ItemInfo`; их `equipment.visualModel` и gender overrides разрешены в 35 существующих `keen::RenderModel` resources.

Ключевые уникальные ссылки hunter:

| Slot | ItemInfo | Item GUID | RenderModel GUID |
|---|---|---|---|
| head | `VC_Body_Head_Male_02_young_african` | `cba24116-4074-41d6-a452-d1ba8db91eec` | `8f02c1cc-d349-4963-8a73-f63b498fdd29` |
| hair | `VC_Hair_05_01_fauxhawk` | `533c1226-dddd-4ddc-a338-22a006452b88` | `098e874d-1847-4d80-9a3e-78aa39428d91` |
| armourHead | `Armor_T4_Ranger_Archer_DPS_Helmet` | `84ff3867-116c-48ec-aef9-c8a6ba33a199` | `13f3b9ae-b04c-423d-af40-acf150a0ece3` |
| armourUpperBody | `Armor_T4_Ranger_Archer_DPS_Chest` | `94404c05-250a-4b14-8c16-283c85391d16` | `0ca2ba0d-95c8-49b9-8599-3d66d38fa9c5` |
| armourLowerBody | `Armor_T4_Ranger_Archer_DPS_Legs` | `cad0997d-e66d-417c-98f6-e03f6745611d` | `66835ac0-9d44-425a-bbe7-cea2597f4101` |
| armourArms | `Armor_T4_Ranger_Archer_DPS_Arms` | `f218d9b0-ef38-49fd-b0a4-3e59d00a19c3` | `d66fab50-cc98-46e7-a523-81c725a35641` |
| armourFeet | `Armor_T4_Ranger_Archer_DPS_Boots` | `3fd4b70c-296c-409d-bb38-5f6795c8d753` | `2c9aefde-3fef-49b7-8ead-865192b7c80c` |

Ключевые уникальные ссылки blacksmith:

| Slot | ItemInfo | Item GUID | RenderModel GUID |
|---|---|---|---|
| head | `VC_Body_Head_Female_10_young_caucasian` | `e79f4c59-5330-472f-b961-73550d717316` | `144b567d-042c-453e-8953-ce3e6b09578c` |
| hair | `VC_Hair_01_06_mohawk_bun` | `0c45d8ae-5509-4a7c-a61f-d862ad4964e5` | `c97d7420-6fa4-48e7-9923-6fce34fd0b3d` |
| armourUpperBody | `Vanity_TX_Blacksmith_Chest` | `1c5f6707-d952-4ae1-85ba-70039214d2f6` | `95c15091-1bf5-4794-baae-35e15fbc1622` |
| armourLowerBody | `Vanity_TX_Blacksmith_Legs` | `fcb90e92-ca36-4879-9c58-9d374ea16f20` | `12eebfdd-0cd3-44dc-bf42-8c891e98ddd9` |
| armourArms | `Vanity_T2_Explorer_Gloves` | `c7ec1f22-7602-4086-b647-3d2e70fcb176` | `b2da1825-2a57-41c9-9540-60b5e275bb79` |
| armourFeet | `Vanity_TX_Blacksmith_Boots` | `b24cd97d-b057-45a5-8681-68f6d4677363` | `c695dbec-5732-41c7-b3bb-5d07d3c89802` |

Shared body slots (`chest`, `collar`, `crotch`, `feet`, `hands`, `lowerArms`, `lowerLegs`, `neck`, `upperArms`, `upperLegs`, `waist`) use stable ItemInfo references. Their `visualModels` contain explicit `Female` overrides; selection therefore depends on the `gender` field. Все 35 target model GUID существуют как `keen::RenderModel`.

## Model / mesh / skeleton

`keen::RenderModel` содержит фактические mesh/LOD arrays, materials, skinning data, joint count и внешний `hierarchy` GUID. У всех 35 target models hierarchy одинаков:

- GUID `87b29df6-6518-43ef-9298-e3f85a6204b9`;
- type `keen::ModelHierarchyResource`;
- ресурс декодирован, `jointNames` и `jointCount` равны 102.

То есть body parts, hair и armor фактически разрешены в RenderModel; mesh данные сериализованы внутри этих resources, а humanoid skeleton hierarchy подтверждён отдельным lookup.

## Evidence graph

```text
TemplateResource
  -> CharacterSetup.presetId                         CONFIRMED_FROM_KFC
  -> CharacterPresetCollection.presets[presetId]     CONFIRMED_FROM_KFC
  -> preset.references.<slot> (ItemInfo GUID)         CONFIRMED_FROM_KFC
  -> ItemRegistryResource itemRefs/dbgNames           CONFIRMED_FROM_KFC
  -> ItemInfo.equipment.visualModel/visualModels      CONFIRMED_FROM_KFC
  -> keen::RenderModel                                CONFIRMED_FROM_KFC (35/35)
  -> RenderModel embedded meshes/LODs/skinning        CONFIRMED_FROM_KFC
  -> ModelHierarchyResource                           CONFIRMED_FROM_KFC (102 joints)

EML clone
  -> same serialized CharacterSetup/references        UNKNOWN
  -> runtime RenderEquipment.lastModels               UNKNOWN
  -> visible entity/render                            UNKNOWN
```

`CharacterPresetRegistry` и `g38_items::ItemRegistry` — runtime singletons. Их сериализованные источники установлены как `keen::CharacterPresetCollection` и `keen::ItemRegistryResource`; отдельный KFC resource с singleton-name не требуется.

## Visual fingerprint

Canonical fingerprint пока не повышается, потому что в нём сравниваются source и EML clone:

```json
{
  "format": "aic_visual_fingerprint_design_v1",
  "source_template_guid": "e3736dff-0ad2-47fc-903c-66c1775836e8",
  "clone_template_guid": "a1c90001-5e4d-4a91-8a1c-000000000001",
  "levels": {
    "STRUCTURAL_MATCH": true,
    "RESOURCE_REFERENCES_MATCH": null,
    "VISUAL_DEPENDENCIES_RESOLVED": null,
    "RUNTIME_RENDER_CONFIRMED": null
  },
  "spawn_ready": false
}
```

Дополнительный вывод `SOURCE_VISUAL_DEPENDENCIES_RESOLVED=true` относится только к двум оригинальным templates и не заменяет clone-level criterion. Следующий load-only тест должен экспортировать у клона `CharacterSetup` и точные preset/item/model paths; runtime render всё равно останется отдельным игровым критерием.
