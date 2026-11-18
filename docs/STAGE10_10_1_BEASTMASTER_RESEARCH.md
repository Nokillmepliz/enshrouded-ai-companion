# Beastmaster — ownership и lifecycle

Bundled **Beastmaster1.18.1**, authors EMF contributors, Lua, server side, disabled by default, depends Lua>=1.25. [Manifest](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/mod.json). Источник/commit тот же официальный EMF, не Nexus описание неизвестного мода.

| Возможность | Source evidence | Что можно использовать |
|---|---|---|
| Tame существующего зверя | [tame.lua](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/tame.lua), [wild.lua](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/wild.lua) | Channel/feed/health eligibility, но это animal-specific flow |
| Spawn вызванного зверя | [pack.lua208](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/pack.lua#L208): emf.spawn, позиция рядом, ally/level, guard event | Структура call/cleanup; сама позиция не safety proof |
| Логический owner | [roster.lua1–8](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/roster.lua#L1): account key, collection/world | Personality/logical companion отделяется от ephemeral entity |
| Instance identity | pack185: `ours` проверяет position, health>0, PlayerAlly faction | Слишком слабая проверка для безопасного destroy; ally не owner token |
| Follow | pack226 StartGuardingEvent; idle/calm восстанавливает guard после combat | Полезно для enemy AI bodies; human villager неизвестен |
| Дружественность/враги | pack27+,125–190; [fight.lua](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/beastmaster/fight.lua), threat.lua | Target policies, PlayerState exclusions, passive/defending/aggressive |
| Recall/дистанция | pack.lua, aside.lua: teleport, временное снятие/повторный вызов | Recovery policy, но не безопасная пространственная гарантия |
| Dismiss | pack455: `if ... ours(...) then emf.destroy(...)` | Не подтверждает атомарное удаление нужного экземпляра |
| Reload | pack72+: старые entity IDs очищаются; roster.serialize | Перепривязка логического состояния, не сохранение instance ID |
| Death | rest/back/active slots, health watch, callbacks | Cooldown/recovery state machine и уведомления |
| Дом/idle | home.lua/idle.lua, stable interactions, animal species config | Зависит от животных/стабла; не переносить как humanoid implementation |

Использовать можно separation roster/runtime IDs, account/session binding, очереди задач и отмену, режимы боя, учёт отсутствия owner. Имена/виды животных, родные AI и pet interactions не решают человеческий render/инвентарь. Направление проекта остаётся humanoid.

MIT корня распространяется на этот source; отдельного license override в папке не найдено. Сохранять notices при переносе существенного кода. Creature packs и сторонние assets надо проверять отдельно; разрешения на игровые meshes не следуют из MIT кода. Сейчас не копировались ни animal assets, ни реализация мода.

Source comments о наблюдавшемся возвращении wolf из idle — upstream observations, не наши игровые тесты и не доказательство универсального follow. Strong ownership/instance generation остаются UNKNOWN/UNAVAILABLE в публичном API.
