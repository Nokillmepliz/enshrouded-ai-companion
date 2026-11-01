# Stage 10.9 — runtime results

- Phase: A, research/offline engineering only.
- Runtime: **NOT_EXECUTED**.
- Game/server launch: **NOT_EXECUTED**.
- Mod install/rollback: **NOT_EXECUTED**.
- Spawn/destroy/entity/faction/inventory/save mutation: **NOT_EXECUTED**.
- `RUNTIME_RENDER_CONFIRMED=UNKNOWN`.
- `spawn_ready=false`.
- Verdict: **NATIVE_EXTENSION_REQUIRED / BLOCKED_FOR_SPAWN**.

Исходники подтверждают public native `spawn_ex`, server session, ECS reads и accepted-call semantics destroy. Они не подтверждают engine generation/ownership marker, read-only position clearance, custom villager persistence, dynamic non-hostility или atomic owned destroy. Офлайн controller реализует fail-closed состояния, но не имеет runtime transport.

Phase B и Phase C не выполнялись и автоматически не разрешены.
