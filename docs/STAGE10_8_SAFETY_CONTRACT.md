# Stage 10.8 — safety contract

Verdict Phase A: **BLOCKED_FOR_SPAWN**. Контракт реализован в [safe_spawn.py](../companion/safe_spawn.py); runtime scaffold [emf_safe_spawn](../experimental/emf_safe_spawn/) выключен и не содержит mutation API.

## Конечный автомат

`DISABLED → PREFLIGHT_REQUIRED → READY_FOR_CONFIRMATION → SPAWN_REQUESTED → ENTITY_ACTIVE → DESPAWN_REQUESTED → ENTITY_REMOVED`.

Любое нарушение переводит controller в `LOCKED`; runtime fault после допустимого запроса — в `FAILED`. Автоматических переходов в spawn, retry, respawn или recovery нет. Reload/reconnect блокирует spawn. `spawn_once` допустим максимум один раз и только после отдельного непосредственного подтверждения пользователя с новым run token.

Phase A не имеет перехода к `SPAWN_REQUESTED`: Python всегда сообщает `spawn_ready=false`, а Lua scaffold отклоняет `spawn_once`, `despawn`, `emergency_stop` как `phase_a_mutation_prohibited`.

## Обязательные gates

- Game: build 1273043; LOCAL `Body Test`/`AI Body Test`, slot 1; dedicated/multiplayer=false; combat явно false; receipt, backup, DAT/LOCAL integrity, Bridge и observer подтверждены.
- Template: точный GUID/type; 81 компонент; fingerprints `412d61b0`/`a7f38d80`; HashKey32/animation/references/source integrity; faction `PlayerAlly (11)`; отсутствие runtime override.
- Entity: один экземпляр; exact instance identity и ownership; faction до spawn; проверяемое исчезновение после адресного destroy.
- Position: walkable surface, geometry clearance, безопасная дистанция, отсутствие боя/врагов/опасной зоны — всё должно быть подтверждено до spawn.
- Persistence: понятный lifecycle `ForceSave`/`ActiveNpcState`, способ обнаружить остаток после reload и доказанный recovery.

Unknown всегда равен FAIL. Кратковременное существование, отсутствие ошибки или `destroy=true` не подтверждают длительное поведение/удаление.

## Текущие блокеры

1. Нет native generation/instance marker и доказанного ownership.
2. Нет public pre-spawn ground/geometry/navmesh query.
3. Persistence villager clone с `ForceSave` неизвестен.
4. Spawnability собственного EML GUID не проверена.
5. Фактическая faction/hostility, model, skeleton и animation требуют runtime.

Первые три блокера не допускают Phase B, даже если все mocks проходят.

## Despawn и recovery

Будущий destroy разрешён только при совпадении текущей session, handle и полного identity fingerprint. Широкие фильтры, удаление по одному npcId/type/GUID и повтор destroy после неопределённого результата запрещены. Принятие native вызова должно сопровождаться тремя последовательными server-callback наблюдениями отсутствия ID.

При потерянном handle, reload, reuse, mismatch или неопределённом spawn controller блокируется и ничего не удаляет. `emergency_stop` не обещает cleanup при crash/Bridge loss; Phase A проверяет его только на mock.

Recovery для будущего эксперимента: закрыть игру вручную, сохранить evidence неудачи, отдельно согласовать восстановление полного verified LOCAL-набора тестового мира и проверить hashes. Текущий Stage 10.7 backup не следует автоматически применять после новых штатных save changes; перед экспериментом нужен новый verified backup.
