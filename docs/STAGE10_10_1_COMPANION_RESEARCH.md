# Companion — исходники и применимость

Реальный bundled mod **Companion1.7.0**, authors EMF, C++, disabled by default. Репозиторий matenm/emf-enshrouded, закреплённый commit `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`. [Manifest](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/companion/mod.json). Это самостоятельный игровой mod, а не библиотека LLM/AI-companion SDK.

Основные доказательства: [companion.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/companion/companion.cpp), [companion_logic.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/companion/companion_logic.h), [orders.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/companion/orders.h), [gear.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/companion/gear.h).

| Вопрос | Подтверждённый механизм / ограничение |
|---|---|
| 1. Создание | `summon`, cpp198–228: api->spawn на player x+2, same y,z |
| 2. Тело | Default Enemy_Vukah_Melee d5d05217-52dc-467a-9192-26b4f661d8d9; не humanoid |
| 3. Custom template | GUID setting есть; совместимость любого GUID с Enemy01 AI не гарантируется |
| 4. Villager | Human villager support не подтверждён; проверяет DynamicEnemy01BehaviorState |
| 5. spawn_ex | Этот summon использует spawn, не spawn_ex; отдельного ownership component не создаёт |
| 6. Entity identity | ID + world/session + template pointer + faction/health/AI; stable instance generation отсутствует |
| 7. Ownership | Собственный g_companion record; это sidecar, не атомарная метка engine instance |
| 8. Follow | guard_program cpp158+: StartGuardingEvent; apply_follow cpp118+ читает Enemy01 guardSetup |
| 9. Дистанция | Nonzero follow_distance пишет shared template, затрагивая других существ того же template |
| 10. Move/catch-up | cpp244–275: teleport с ground; при отказе destroy+новый spawn; не безопасный универсальный lifecycle |
| 11. Target/combat | AddThreatTargetEvent и штатный Enemy AI, order Attack; humanoid combat не доказан |
| 12. Stay | Order marker, отдельный spawned object; добавляет собственные cleanup риски |
| 13. Inventory | Собственного ECS inventory у тела нет: gear.h2–6, sidecar held pieces |
| 14. Equipment | take_items/put обратно, id/level/rarity и бонус уровня; полноценный RenderEquipment не реализован этим кодом |
| 15. Faction | cpp100–113,218,366+: server и client Faction, повторное применение; недоступный компонент логируется |
| 16. Persistence | cpp406–434: per-world slot sidecar, order/gear/out; не доказательство сохранения самой entity |
| 17. Reload | cpp762–769: server_session reset, marker ids забываются; file/session binding |
| 18. Dismiss | request_stop → take_destroy → api.destroy cpp786; true означает результат API, не observed absence |
| 19. Despawn/потеря | presence health/template/faction; retries policy и ограничение потерь; нет generation guard |
| 20. Duplicates | Phase Active/None/stop предотвращает обычный повторный вызов; замена после destroy без подтверждения удаления остаётся риском |
| 21. Death | EntityDiedEvent, health checks, respawn policy; respawn_seconds default0 |
| 22. Пределы | safe position до spawn, atomic delete, человеческий render, open-world villager follow и LLM не подтверждены |

Фракция и template pointer могут совпасть у повторно использованного ID. Поэтому Companion не закрывает IDENTITY/OWNERSHIP/DESTROY gates нашего проекта. В gear.h прямо предусмотрен crash-сценарий возможного дублирования предмета; это не подходящая готовая транзакционная гарантия для нашего inventory.

Повторно использовать целесообразно идеи order state machine, session-bound queues, timeout UX, serialization и тестовые сценарии; переносить mutation-код без наших guards нельзя. Не включать upstream Companion одновременно с нашим adapter: оба могут создавать тела/markers и менять поведение.

Лицензия: корневой [MIT](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/LICENSE), copyright2026 EMF contributors; отдельной лицензии мода не обнаружено. При копировании существенного кода сохранять copyright/license notices. В этой фазе upstream код не копировался в продукт и не устанавливался. Версия в source manifest не доказывает совпадение shipped DLL и source.
