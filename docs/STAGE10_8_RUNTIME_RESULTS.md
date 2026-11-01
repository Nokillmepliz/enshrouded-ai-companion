# Stage 10.8 — runtime results

**NOT_EXECUTED**

Phase A не запускала Enshrouded/server, не устанавливала `aic_safe_spawn`, не вызывала spawn/despawn, не выполняла rollback и не изменяла KFC/resources, DAT/KSD или LOCAL saves.

Итог исследования: **BLOCKED_FOR_SPAWN**. `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

Блокеры: точная instance identity/ownership, pre-spawn безопасная позиция и persistence humanoid villager с `ForceSave`. Spawnability собственного template GUID, фактическая faction, render, skeleton, animation и despawn verification также требуют отдельного игрового эксперимента после закрытия первых блокеров.
