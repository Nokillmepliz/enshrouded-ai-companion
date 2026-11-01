# Stage 10.9 — минимальный EMF native extension (design only)

Статус: **NATIVE_EXTENSION_REQUIRED / DESIGN_ONLY**. Это не существующие API EMF. DLL, hooks, offsets и runtime calls не реализованы и не устанавливались.

## Граница решения

Extension — отдельный native EMF mod namespace `aic.spawn_safety.v1`, API 20+, pinned Enshrouded build 1273043 и pinned EMF 0.3.2 binary hash. Он регистрирует только явные команды/вызовы, не имеет autostart, tick-spawn, background retry или самостоятельного recovery. Любая неизвестность возвращает ошибку и ничего не меняет.

Public EMF native API уже даёт world callbacks, component reads, entity enumeration, `spawn_ex` и destroy. Он не даёт entity generation, custom ownership type, read-only collision/navmesh query или atomic identity-check-and-destroy. Поэтому extension нельзя считать реализуемым только тонкой Lua-обёрткой.

## Предлагаемый ABI

Имена ниже проектные:

```text
inspect_entity_identity(world, entity_id, expected_session?)
  -> {session_id, entity_id, entity_generation?, template_guid?, instance_token?,
      ownership_proven, state, component_fingerprint}

validate_spawn_position(world, player_entity, forward_xyz, humanoid_capsule,
                        max_distance)
  -> {VALID|INVALID|UNKNOWN, candidate_xyz, ground_hit, surface_normal,
      collision_clearance, walkable, safe_distance, area_available,
      danger_clear, world_session, evidence}

spawn_owned_humanoid(world, template_guid, validated_position_receipt,
                     instance_token, expected_session)
  -> {created, identity, faction_observed, persistence_profile}

destroy_owned_humanoid(world, complete_identity, expected_session)
  -> {accepted, identity_checked_atomically, reason}

inspect_entity_persistence(world, complete_identity)
  -> {components, unique_registry_state, save_classification, status}
```

`instance_token` — 128-bit unpredictable value generated before the operation. A marker must be attached in the same engine create transaction and readable later without broad search. Если engine не предоставляет безопасный component type/lifecycle hook, `spawn_owned_humanoid` возвращает `IDENTITY_MECHANISM_UNAVAILABLE`. Sidecar map `EntityId → token` без engine generation не подходит: он не отличает reused ID.

## Ошибки

`UNSUPPORTED_BUILD`, `WRONG_WORLD`, `STALE_SESSION`, `INVALID_ARGUMENT`, `TEMPLATE_NOT_FOUND`, `TEMPLATE_IDENTITY_UNKNOWN`, `POSITION_INVALID`, `POSITION_UNKNOWN`, `GROUND_QUERY_UNAVAILABLE`, `CLEARANCE_QUERY_UNAVAILABLE`, `OWNERSHIP_MARKER_UNAVAILABLE`, `ENTITY_GENERATION_UNAVAILABLE`, `IDENTITY_AMBIGUOUS`, `ENTITY_REUSED`, `ENTITY_LOST`, `FOREIGN_ENTITY`, `PLAYER_ENTITY`, `PERSISTENCE_UNKNOWN`, `FACTION_MISMATCH`, `SPAWN_REFUSED`, `DESTROY_REFUSED`, `POSTCONDITION_UNVERIFIED`, `NATIVE_FAULT`.

Ни одна ошибка не разрешает fallback на raw coordinates, EntityId-only destroy, wide search, hostile template или retry.

## Технические исследования до реализации

1. Найти поддерживаемый engine identity primitive или доказать безопасную регистрацию custom marker.
2. Найти ABI read-only ground/normal/capsule/path queries; не использовать teleport mutation.
3. Проверить thread/atomicity boundary: check и destroy должны исполняться в одном world callback без промежуточного engine step.
4. Определить template identity entity и lifecycle registration без непроверенных offsets.
5. Покрыть C++ pure helpers и fake API; затем отдельный code review/Cargo не требуется, это C++ EMF SDK.

Если пункт 1 невозможен, extension не должен предоставлять spawn. Никаких memory writes/native hooks на Phase A не создано.
