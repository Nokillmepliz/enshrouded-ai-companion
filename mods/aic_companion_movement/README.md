# Companion Movement 0.1.1 — one manual move

Disabled by default in mod.json; prepared update, not installed by preparation.
`main.lua` enables the explicit move_to handler; loading it never sends a move.
No spawn/destroy, component writes, home edits, save APIs or spawn latch/intent
access. See [manual movement plan](../../docs/STAGE10_12_MOVEMENT_TEST.md).

`discover`/`status` are read-only commands using the existing Python Bridge.
The Lua controller implements a gated one-order `move_to` using EMF
0.6.18 API46 `villager_move`. A unique npcId/component profile is NOT proof of a
template GUID or persistent instance identity. Installation and runtime testing
require separate authorization. CLI targets the player's sampled standing
position, 2–5 m from the NPC, and requires typing MOVE after inspecting it.
Daylight/clear solid ground are operator checks; wall/height/awake/unique NPC and
existing-order checks run before native API. EMF validates home radius/leash and
uses its own navigation. Timeout/stuck can issue a native stop-position event.
No hold/follow, teleport, retries or explicit cancel. Do not reload the mod or
delete the movement intent to bypass a consumed/uncertain attempt.
