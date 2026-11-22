# Companion Movement 0.3.0 — Stage 10.14 (offline)

Approach the player using native villager navigation, not a replay of player motion.
No installation or game test performed. Current deployed version remains 0.2.1.
Do not reuse the spent Stage10.13 runner. Stage10.14 has a separate reviewed
follow-stage10-14.lock and exclusive journal; old SPENT remains unchanged.
Installation and the new runtime session require separate authorization.

Eight destination candidates at 1.8m around the player. Ground/Path failures and
explicit move refusals rotate candidates after 4s; ambiguous results stop.
No height/fall-damage veto. Direct walls are diagnostic: native Path may find a
detour. Jumps=true, max_jump_up/down=0; path nodes0/2/3/4 accepted. Villager_move
chooses and executes its own route: a found jump path is NOT proof it can jump.
No custom pathfinding, jump, glide, teleport or component writes.

Moving player/NPC does not invalidate a destination snapshot. Path origin is
refreshed after Ground. Before ordering, check path freshness4s, usefulness and
player occupancy. Retarget active orders only after player displacement>8m and
>=8s. Idle2m/resume2.8m in3D; horizontal activation<=20m, deactivation>50m. Home/leash still apply.

Limits:180s session,30 probes(one in flight),24 order attempts,2 stuck/timeout
recoveries,4s heartbeat. Orders30s/stuck8s/arrive0.5m, optional hold5s. Sleep/busy
waits within session deadline. Native roaming remains enabled. Lost identity,
foreign order, unknown move/cancel and unreturned-query timeout stop the session.
Durable latch/journal and existing spawn intents remain intact. No reset/rearm.

PROGRESS logs distance to player/target and displacement. Terminal reason is
preserved. Accepted is not arrived; STUCK is not success. PROFILE_ONLY identity.
See docs/STAGE10_14.md for source evidence, limitations and the proposed test.
