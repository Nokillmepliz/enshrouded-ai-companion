# Experimental EML humanoid template

Это data-only patch **0.4.0** для проверяемого EML 0.2.0. Он клонирует `hunter_assistant` в новый `TemplateResource`, задаёт отдельные GUID/npcId и faction `PlayerAlly`, но не создаёт игровую сущность. Исходный story template не изменяется.

Capability `export` создаёт `aic_eml_humanoid_evidence_v4`. Девять `HashKey32` читаются через отражённое поле userdata `.value`; EML преобразует внутренний `UInt32` в точный Lua integer. Экспорт содержит source/clone values и provenance, component fingerprint, animation/retarget, visual baseline и read-only lookup результата `game.assets.get_resource`.

`game.assets.create_resource` регистрирует составной ключ GUID/type/part в EML AppState. Отдельная запись в `GuidRegistryResource` этим API не требуется, поэтому patch не изменяет такой registry. Успех EML lookup не доказывает загрузку ресурса игрой или возможность spawn.

`src/mod.lua` содержит `__AIC_STAGE10_RUN_TOKEN__`. Будущий штатный installer должен заменить placeholder новым 128-bit token, общим с observer и receipt. Исходник с placeholder fail-closed.

Patch не содержит spawn, entity-команд или доступа к сохранениям. `runtime_enabled=false`; `spawn_ready=false`. Evidence v3 остаётся читаемым evaluator/observer только как исторический совместимый формат и не может пройти новые H/R gates.

Офлайн-проверка:

```powershell
.\.tools\python\python.exe -m unittest tests.test_eml_humanoid tests.test_stage10_6 tests.test_stage10_7 -v
```

Реальная установка 0.4.0, rollback текущей 0.3.0 и игровой load-only тест требуют отдельного разрешения.
