# First humanoid visual experiment — 0.1.1

Experimental controller for EMF 0.6.18 / API46 / Lua1.39, build1287369,
patch0.5.1. Separate from the unchanged read-only observer.

No automatic spawn, respawn, destroy, faction writes, save edits, teleport,
combat, follow or inventory operations. One hardcoded GUID only.

Deploy only after separate approval using the reviewed exact manifest. The
initial package builder created private binding.lua and an UNUSED attempt.lock.
The 0.1.1 update replaces only mod.json, main.lua, controller.lua and README.md;
it preserves binding.lua, attempt.lock and configuration byte for byte.
Never delete/reset/copy back the latch or Python spawn-intent journal to retry.
No EXE, DLL, native extension, content patch or shadow cleanup is included.

Use scripts/smart_spawn_position.py with the pinned plan and installation receipt.
The Python caller verifies build, mods, LOCAL names/slots/storage, PID and player;
Lua verifies session, server callback, one local player, character and proximity.
Lua does not independently expose world slot/storage: direct manual console
invocation is outside this reviewed interface. The key is a local capability,
not protection against a malicious user who already has console access.

Search performs at most eight overlapping Ground requests, at 45-degree intervals
on a 4m ring (inside the permitted 3–5m range). All Ground callbacks must drain
before sequential Wall/Path checks; choose the first passing direction from +X.
There is never more than one pending Path request. Ground/Path cannot be cancelled
through the confirmed API: a timeout retains the pending count and blocks a new
batch until callbacks arrive. An API exception with unknown submission blocks too.
Ground API acceptance/result, requested/actual XYZ, height delta, fog and water
are logged as AIC_POSITION records. A failed callback's y=0 is marked unmeasured.
Search is read-only; it does not create an entity. Spawn uses ground height +0.1m.
Read the selected position
and visually confirm open, level, dry terrain, away from enemies/buildings/drops.
The probe and confirmation expire after 20s; the player must stay within 0.25m.
Unavailable ground, fog unknown/shroud, reported deep water, path failure,
non-walk moves, approximate endpoint >0.5m or building hit fail closed.
The same session may be searched again only by a new explicit CLI invocation,
after the prior search is settled and hash-sealed, all callbacks drained,
no durable intent exists and the latch is still UNUSED. Nonces are never reused.
No automatic search loop or automatic spawn retry exists. Histories are retained.
At READY, fresh local Y permits one spawn; N/ESC or deadline cancels. Buffered or
held Y before READY is discarded. The 20s deadline starts at probe, not READY.
Before spawn, Python revalidates session/probe/deadline/context and Lua revalidates
player displacement, deadline, existing candidates and Wall. Ground/Path evidence
must still be within that same 20s window; it is not a continuous terrain monitor.
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
