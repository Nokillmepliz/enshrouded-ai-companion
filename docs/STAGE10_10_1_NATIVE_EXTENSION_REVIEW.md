# Минимальное расширение и варианты тела

Уточнение Stage10.9: собственные дубликаты ground/path/villager movement больше не нужны. Подтверждены native API34 ground_at,37 path_find/path_cancel,44 block_at/find_wall,46 villager_move. [SDK API](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/emf_api.h), [Lua bindings](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/bindings.cpp).

ground_at — asynchronous server query в загруженной области, не capsule clearance/normal/hazard proof. path_find — ограниченная read-only path query, FOUND может вернуть ближайшую достижимую точку, сама NPC не двигает. block_at/find_wall относятся к построенным блокам; false может означать недоступность, а не безопасность позиции. villager_move — bounded walk/leash, не готовый open-world follow.

`change_component` допускает только upstream allowlist; ForceSave/DoNotSave/LifeTime/IsTame запрещены для нашего этапа. `spawn_ex` ([spawn.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/spawn.cpp#L66)) добавляет до15 существующих components, не регистрирует безопасный custom ownership marker. `destroy` ([api.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/api.cpp#L852)) принимает uint32 ID, не expected generation. Ни Companion, ни Beastmaster, ни Villager Jobs этого не меняют.

| Вариант | Плюс | Ограничение / решение |
|---|---|---|
| Custom EML hunter clone | Независимое humanoid тело, контролируемый template | Основной кандидат; сначала clean/load/render/lifecycle gates |
| Существующий villager | Уже имеет человеческий visual/native movement | Не независимое новое тело, затрагивает quest/game NPC; не включать без отдельного разрешения |
| Новый native villager | Может использовать native save/AI | Нужны уникальные npcId/template и доказанная persistence; не обход clone audit |
| Upstream Companion | Готовые orders/guard/sidecar | Vukah/EnemyAI, не подмена humanoid направления |
| Собственный native extension | Может дать недостающий instance proof | Только при найденном engine primitive; интерфейс сам по себе не доказательство |
| Hybrid | EML humanoid + EMF APIs + Lua controller + Python Brain | Рекомендуем; reuse по контрактам, minimal native gap only |

**NATIVE_EXTENSION_STILL_REQUIRED** условно для прежнего требования атомарного ownership-checked spawn/destroy, пока upstream не предоставит необходимый primitive. Реализовать его честно сейчас нельзя: stable generation/instance GUID/atomic owner comparison не подтверждены. Не ослабляем gate и не объявляем pointer/npcId/SpawnTime полноценным решением. Для visual-only load проверки extension не требуется; spawn review — отдельная граница.

Оставшиеся native gaps: доказуемая instance identity и ownership; atomic conditional destroy с observed result; полная pre-spawn clearance/danger semantics; custom-villager save/despawn policy. Stage11 implementation не начат, DLL/hooks/memory writes не добавлены.
