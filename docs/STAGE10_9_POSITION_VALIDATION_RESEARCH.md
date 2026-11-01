# Stage 10.9 — pre-spawn position validation

Дата: 2026-11-01. Runtime не выполнялся.

## Доступные механизмы

Public `spawn` принимает готовые координаты и создаёт только `CurrentTransform`: [spawn.cpp L53–64](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L53-L64). Lua API не предоставляет ground, collision, capsule, navmesh или walkability query перед созданием entity.

EMF teleport использует игровой `Teleport.searchBestSpawnPosition`. Комментарий исходника описывает ближайшую walkable cell примерно в 10 м, но при отсутствии результата игра использует raw target; EMF отмечает это `kTpRawTarget`: [teleport.h L61–76](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/teleport.h#L61-L76). Механизм требует уже существующую entity, добавляет ей компонент `Teleport` и наблюдает перемещение до 10 секунд: [teleport.h L2–17](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/teleport.h#L2-L17). Это mutation и не является read-only pre-spawn query.

ECS program map подтверждает внутренние `ColliderSystem`, `PathGridSystem`, `VoxelGrid` и EntityGrid, например в wildlife: [ecs_programs.md L825–827](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L825-L827). Он доказывает существование подсистем, но не стабильный вызываемый ABI для capsule clearance, surface normal или navmesh lookup. Неизвестные offsets/vtables не используются.

| Проверка | Public EMF | Internal evidence | Статус |
|---|---|---|---|
| допустимые числовые/world bounds | teleport helper | `check_request_numbers` | CONFIRMED |
| ground/walkable search | только mutation teleport | game teleport program | PARTIAL |
| surface normal | нет | не найден стабильный ABI | UNKNOWN |
| humanoid capsule clearance | нет | ColliderSystem существует | UNKNOWN |
| navmesh/path reachability | нет | PathGridSystem существует | UNKNOWN |
| terrain streaming/server availability | нет отдельного query | встречается в game systems | UNKNOWN |
| враги/опасная зона | entity scan частично возможен | классификация угроз неполна | UNKNOWN |

## Контракт validator

`validate_spawn_position()` в `companion/safe_spawn.py` принимает identity мира и доказательства `ground_hit`, `surface_normal`, `collision_clearance`, `walkable`, `safe_distance`, `area_available`, `height_ok`, `danger_clear` с provenance. Результат — `VALID`, `INVALID` или `UNKNOWN`.

- Любой явный отрицательный результат даёт `INVALID`.
- Любое отсутствующее доказательство или provenance даёт `UNKNOWN`.
- Только все подтверждённые проверки дают `VALID` в офлайн-модели; mocks не подтверждают runtime.
- `UNKNOWN` блокирует spawn.

Spawn с последующим teleport запрещён как замена предварительной проверке: опасная entity уже существует до teleport. Минимальному native extension нужен read-only query, закреплённый за build 1273043, который возвращает ground hit/normal, humanoid clearance, walkability и world/session identity. Сейчас gate `POSITION=UNKNOWN`.
