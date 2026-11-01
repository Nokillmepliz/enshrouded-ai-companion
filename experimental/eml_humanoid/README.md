# Experimental EML humanoid template

Это data-only patch **0.3.0** для проверяемого EML 0.2.0. Он клонирует `hunter_assistant` в новый `TemplateResource`, задаёт отдельные GUID/npcId и faction `PlayerAlly`, но не создаёт игровую сущность. Исходный story template не изменяется.

Capability `export` создаёт `aic_eml_humanoid_evidence_v3`: полный typed `CharacterSetup` source/clone, animation/retarget, component fingerprint, pinned visual-reference baseline, registry/source-integrity и provenance. `ModelResource` и runtime `RenderEquipment.lastModels` не считаются обязательными. Завершение writer, загрузка игры и runtime render подтверждаются отдельно.

`src/mod.lua` в репозитории содержит `__AIC_STAGE10_RUN_TOKEN__`. Штатный installer заменяет его новым 128-bit token, общим с observer и ignored install receipt. Исходник с placeholder fail-closed.

Patch не содержит spawn, entity-команд, доступа к сохранениям или runtime Body Adapter. Descriptor сохраняет `runtime_enabled=false`; `spawn_ready=false`. Установка patch сама по себе не доказывает загрузку template, визуал entity, ownership или безопасный dismiss.

Офлайн-проверка:

```powershell
.\\.tools\\python\\python.exe -m unittest tests.test_eml_humanoid tests.test_stage10_6 -v
```

Read-only observer использует evidence v3 и сообщает ограничение публичного EMF Lua: `UNAVAILABLE_WITHOUT_ENTITY`. Load-only A/V/B/C проверяется отдельно и не разрешает spawn.
