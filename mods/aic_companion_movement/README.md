# Companion Movement 0.1.0 — offline prototype

Disabled by default; not installed. `main.lua` also locks movement with
`allow_move=false`. No spawn/destroy, component writes, home edits, save APIs or
spawn latch/intent access. See [Stage 10.12](../../docs/STAGE10_12.md).

`discover`/`status` are read-only commands using the existing Python Bridge.
The Lua controller implements a gated one-order `move_to` prototype using EMF
0.6.18 API46 `villager_move`. A unique npcId/component profile is NOT proof of a
template GUID or persistent instance identity. Movement activation and testing
require a separate review/authorization; do not edit the gate during a live game.
