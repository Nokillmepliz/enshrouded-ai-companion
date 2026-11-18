# Villager Jobs — человеческое тело и движение

Bundled **Villager Jobs1.5.3**, C++, author EMF, minimum nativeAPI20, disabled by default. [Manifest](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/villager_jobs/mod.json). Source pinned EMF `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`, MIT root, отдельного license override нет.

Он назначает работу уже существующим villagers, а не создаёт нового человеческого компаньона. [villager_jobs.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/villager_jobs/villager_jobs.cpp): `npc_id_of`256, `lookup`267, `with_identity`275, `candidates`548. NPC выбирается по подтверждённым villager components, позиции и ActiveNpcState npcId. После reload entityId может измениться; npcId/место помогают восстановить job, но не являются универсальным instance generation.

Движение `send_npc_to`493: transform → queued npcId/target → [GoToPosition event emission](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/mods/villager_jobs/villager_jobs.cpp#L908). Мод не следует автоматически считать клиентом нового `villager_move`: `moved_elsewhere`490 только уступает API46 `villager_moving`, чтобы очереди не конфликтовали.

`jobs_logic.h` хранит jobs, work timers, ожидание материалов, rebind, stuck recall; `save_jobs/load_jobs`560–596 и server_session880+ сбрасывают queued действия старого мира. Cancel снимает job; это не эквивалент удаления villager. Farm/tend/haul/craft/gather реализованы вокруг chests/локальной работы; эти mutations здесь не включаются.

Новый [core/villager_moves.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp#L140) проверяет walk area/home leash, ограничивает points, обрабатывает STUCK/TIMEOUT/ARRIVED/GONE/CANCELLED; ожидание busy/night/близкого игрока не равно успеху. Строки148–164 отклоняют маршрут за пределами home leash;270 обнаруживает teleport как stuck;301/347 приостанавливают timers. Значит локальная навигация **не доказывает open-world follow**.

Для custom humanoid потребуется совместимый ActiveNpcState/AI/walk setup; наличие модели и npcId недостаточно. Source hunter/blacksmith clone в mixed database не доказывает пригодность этих jobs к нашему телу. Повторно использовать: job queue/cancel/rebind design, cooperation с villager_moving, diagnostics/wait states, часть подходов к chest transfer после отдельного inventory этапа.

Риск raw layout: ActiveNpcState template npcId читается через guarded_copy по известному layout. После update это требует новых reflection/schema checks; не переносить offset assumptions как стабильный API.

Дополнительно найдены Necromancer (другие enemy/pet bodies), Handover/Quick Stack (item transfer), content creature packs. Они не предоставляют доказанный humanoid lifecycle или AI Brain. Их включение/перенос кода не предлагается без отдельного bounded audit.
