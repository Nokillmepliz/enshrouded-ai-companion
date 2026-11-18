# First humanoid visual experiment — 0.1.0

Experimental controller for EMF 0.6.18 / API46 / Lua1.39, build1287369,
patch0.5.1. Separate from the unchanged read-only observer.

No automatic spawn, respawn, destroy, faction writes, save edits, teleport,
combat, follow or inventory operations. One hardcoded GUID only.

Deploy only after separate approval using the reviewed exact manifest. The
package builder creates private binding.lua and an UNUSED attempt.lock.
Never delete/reset/copy back the latch or Python spawn-intent journal to retry.
No EXE, DLL, native extension, content patch or shadow cleanup is included.

Use scripts/experimental_spawn.py with the pinned private client-binding.json.
The Python caller verifies build, mods, LOCAL names/slots/storage, PID and player;
Lua verifies session, server callback, one local player, character and proximity.
Lua does not independently expose world slot/storage: direct manual console
invocation is outside this reviewed interface. The key is a local capability,
not protection against a malicious user who already has console access.

prepare performs asynchronous ground/path queries only. Poll status explicitly.
The candidate is 4m along world +X, ground height +0.1m at spawn. Read the position
and visually confirm open, level, dry terrain, away from enemies/buildings/drops.
The probe and confirmation expire after 20s; the player must stay within 0.25m.
Unavailable ground, fog unknown/shroud, reported deep water, path failure,
non-walk moves, approximate endpoint >0.5m or building hit fail closed.
find_wall=nil is NOT proof of free space; path-grid clearance is approximate,
shallow water and dynamic obstacles still require manual inspection.

spawn additionally requires I_APPROVE_ONE_DISPOSABLE_SPAWN plus explicit manual
clear-area and persistence-risk acknowledgments in Python. A fsynced exclusive
Python intent and verified Lua latch write precede the single API attempt.
Lua flush is not a power-loss durability guarantee. Keep both guards and their
history. Crash/0/timeout means UNKNOWN: no retry, no destroy by ID.

observe reads the returned candidate only. npcId/faction/component agreement is
not ownership or instance generation. It never mutates even on ID reuse.
No continuous controller AI is running. Use separate read-only observations
over 30–60 seconds and the user's screenshot/checklist. Entity presence is not
proof of rendering or peaceful behavior.

Manual game closure ends the live experiment, NOT proven cleanup. The template
contains ForceSave/ActiveNpcState/ActiveNpcStateSaved. Treat Body Test / AI Body
Test as disposable, preserve failed-run evidence, and do not reload until review.
Restore the full verified LOCAL set only after separate authorization. Closing
can save the NPC; killing the process does not guarantee avoiding autosave.

experimental_spawn_executed=false until an explicitly authorized attempt;
production_spawn_ready=false; spawn_ready=false; render UNKNOWN.
