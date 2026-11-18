# Stage 10.10 — пересмотр Stage 10.9

Сравнение API20/EMF0.3.2 с API46/EMF0.6.18, commit `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`.
Ни один API не вызывался в игре. Старые отчёты остаются историческими.

| Вывод / функция Stage 10.9 | Новый статус | Основание |
|---|---|---|
| EntityId — uint32, reuse возможен | STILL_VALID | EXE reflection: 4 bytes; destroy всё ещё принимает только id |
| public entity generation / stable instance GUID | UNKNOWN | в public ABI46 не найдены; query/callback generation не идентичность entity |
| собственный ownership marker / atomic compare-and-destroy | STILL_VALID blocker | API destroy не принимает expected template/generation/owner |
| spawn_ex до 15 компонентов | STILL_VALID | spawn.cpp добавляет CurrentTransform + до 15 extra, identity orientation |
| отсутствие read-only ground query | SUPERSEDED_BY_NEW_API | API34 ground_at, Lua1.26 |
| отсутствие read-only path query | SUPERSEDED_BY_NEW_API | API37 path_find/path_cancel, Lua1.29 |
| полный pre-spawn position safety | REQUIRES_REVALIDATION | ground/path не дают весь capsule clearance, surface normal и danger contract |
| generic raycast/physics overlap | UNKNOWN | есть voxel-ground и building-only find_wall, универсального ABI не подтверждено |
| ForceSave/DoNotSave dynamic mutation | STILL_VALID blocker | change_component API23 существует, но эти типы пока refused |
| unique villager / ActiveNpcStateSaved lifecycle | REQUIRES_REVALIDATION | новые source values, нет теста custom clone save/reload/despawn |
| пассивный humanoid / faction11 | REQUIRES_REVALIDATION | serialized PlayerAlly не доказывает runtime peaceful behavior |
| ручная реализация villager movement | SUPERSEDED_BY_NEW_API | API46 villager_move, Lua1.39; действует в разрешённой walk area |
| Python safety controller | STILL_VALID как offline model | runtime bindings/новый profile не подтверждены; gates не ослаблены |
| весь прежний native extension scope | REQUIRES_REVALIDATION | ground/path/move уже upstream; оставлять только доказанные пробелы |

Точные исходники:

- [ground_at, path_find, block_at/find_wall, villager_move](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/emf_api.h#L1532-L1697).
- [Lua ground binding](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/map_bindings.cpp#L232-L252), [path binding](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/path_bindings.cpp), [villager binding](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/move_bindings.cpp#L210-L296).
- [spawn implementation](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/spawn.cpp#L66-L128), [destroy и player guard](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/api.cpp#L852-L868).
- [change_component allowlist](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/reference.md#L470-L496), [unique NPC research](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/engine_parts/ai.md).

`ground_at` асинхронен, зависит от загруженной области и build availability,
отличает ground/not-loaded/failed, fog unknown и water. `path_find` ничего не
перемещает, ограничен 200 m и 32 queries; `FOUND` с closest не гарантирует reaches.
`find_wall=false` может означать и отсутствие блока, и unavailable/not-loaded;
оно не является доказательством свободной капсулы. `villager_move` ограничен walk
area/leash, может WAIT/STUCK/TIMEOUT и не равен проверенному follow нашего clone.

Построены и выполнены 30 upstream C++ тестов ground/search/path на fake dependencies:
730 assertions PASS. Это подтверждает сервисные алгоритмы, не engine ABI на машине
пользователя. Собственный native extension пока не реализуется; потребность в
надёжной instance identity и атомарной проверке удаления остаётся, но его scope
надо заново согласовать после load-only acceptance. Stage 11.0 не начат.
