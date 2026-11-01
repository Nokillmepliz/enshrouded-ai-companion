# Этап 10.5 — состояние visual dependencies после контрольной точки A

Статус: **данные ресурсов не извлечены**. Этот документ фиксирует границу доказательств после аудита inspector и не заменяет будущий KFC report.

## Ресурсы

| Объект | Статус | Доказательство |
|---|---|---|
| `hunter_assistant` `e3736dff-0ad2-47fc-903c-66c1775836e8` | `NOT_EXECUTED` в KFC Inspector | Только EML evidence 10.2 и source-level ECS research |
| `blacksmith_assistant` `04d42ed2-beb4-4013-8f10-5d63efae2015` | `NOT_EXECUTED` | Известен только GUID |
| `aic_eml_humanoid` | ожидаемо отсутствует в original KFC | Создаётся EML patch |
| `CharacterPresetRegistry` | `UNKNOWN` | Type/GUID/serialization не подтверждены |
| `ItemRegistry` | `UNKNOWN` | System registry подтверждён source map, KFC resource не найден |
| Model/mesh/skeleton GUID | `UNKNOWN` | Lookup не выполнялся |

## Граф доказательств

```text
hunter TemplateResource
  -> six visual ECS components                 CONFIRMED_FROM_EML_EVIDENCE
  -> CharacterSetup HashKey32 values            UNKNOWN (не экспортированы)
  -> CharacterPresetRegistry                    CONFIRMED_FROM_SOURCE as system input
  -> Equipment / ItemRegistry                   CONFIRMED_FROM_SOURCE as system chain
  -> RenderEquipment.lastModels                 CONFIRMED_FROM_SOURCE as runtime output field
  -> concrete model / mesh / skeleton resources UNKNOWN
```

Ни одно ребро к конкретному resource GUID не повышено до `CONFIRMED_FROM_KFC`. `HashKey32` не интерпретируется как GUID. Пустые runtime arrays до entity creation не будут считаться отсутствием ресурса.

## Visual fingerprint

Текущий canonical contract повторно сформирован из сохранённого structural evidence:

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
  "spawn_ready": false,
  "canonical_sha256": "9c73c1dd877ccbf11c2e1f9a35fb4bdddc3f6744add747e77a0a930c4ee08724"
}
```

Уровни не изменились. Inspector audit не является чтением ресурса и не доказывает render. EML patch, observer и Stage 10 evaluator оставлены без изменений.

Следующий load-only эксперимент пока не готов: сначала нужно безопасно собрать inspector, извлечь непустой полный список source references и фактически разрешить обязательные зависимости. Даже после этого clone references могут остаться `UNKNOWN`, если старый EML evidence их не содержит; тогда потребуется отдельный load-only export подтверждённых field paths без spawn.
