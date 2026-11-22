# Companion Movement 0.3.1 - Stage 10.15

Prepared offline for build 1287369 / EMF 0.6.18. Not installed or validated in game.
The deployed version remains 0.3.0 until separate approval.

Armed Follow temporarily sets only the unique companion NpcCommon.sleepTime=25
and wakeUpTime=-1 hours. Exact-build static inspection confirms the predicate
sleep = tod >= sleepTime OR tod <= wakeUpTime. These finite bounds exclude all
normal time-of-day values, including midnight. Equal hours do NOT disable sleep.
The engine performs wake/exit/animation transitions; no raw state/actor writes.

Original hours are journalled before either field write. Sleep exit reroll is
reapplied once after observing the transition. Unknown writes stop the session.
Awake must be observed within 15 seconds. Stop/error/heartbeat expiry restore
owned fields. Reload restores the same-session pending lease; it never resumes
Follow. Ambiguous identity prevents restoration into an unverified entity.
Stop and verify SCHEDULE_RESTORED before disabling the mod. There is no verified
unload callback after forced Lua unload. Preserve the schedule journal.

Unchanged: X/Z activation <=20m, deactivation >50m, 3D proximity2m/resume2.8m,
native Ground/Path/villager_move, eight candidates,180s,24 orders,30 probes,two
recoveries. No teleport/custom pathfinding/height veto/home/faction/inventory
or spawn changes. Native home/leash/sitting/talking constraints still apply.
Roaming is not globally disabled; accepted orders are not proof of movement.

NEW Stage10.15 lock, schedule journal and Python journal; preserve all old
SPENT/intent/history. Commands remain <=32 characters. PROFILE_ONLY identity.
See docs/STAGE10_15_IMPLEMENTATION.md and exact update manifest. spawn_ready=false.
