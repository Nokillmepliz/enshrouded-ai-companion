# Companion Movement 0.3.5 - responsive target updates

Prepared offline for build 1287369 / EMF 0.6.18. Not installed or validated in game.
The deployed version remains 0.3.4 until separate approval.

This is a responsiveness fix, NOT a removal of the native home restriction.
Retarget after >3m player displacement and >=2s, queue native cancellation in a
fresh tick, wait for confirmation before another order. Dispatch spacing is1s;
refused destinations still back off4s. Anchor retarget to the player sample used
for the destination query. All order/query/recovery budgets remain unchanged;
frequent direction changes can exhaust them before205s.

After arrival the existing native hold keeps the accepted goal for at most5s.
When the player moves beyond2.8m, the responsive profile releases that hold
through the same deferred cancellation. No saved roaming parameters are changed;
native roaming can resume after hold expiration or stop.

Read-only nav_info reports template radius, saved override/radius, effective
radius, home and native leash. Runner records these before its one start.
It never writes these fields or silently expands the permitted movement area.
The previous runtime had six refusals outside10m from home; speed changes alone
cannot fix that. A content/template change needs separate preparation and review,
and runtime readback must distinguish the template from a saved override.

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
native Ground/Path/villager_move, eight candidates,210s,24 orders,30 probes,two
recoveries. No teleport/custom pathfinding/height veto/home/faction/inventory
or spawn changes. Native home/leash/sitting/talking constraints still apply.
Roaming is not globally disabled; accepted orders are not proof of movement.

NEW Movement0.3.5 lock, schedule journal and Python journal; preserve all old
SPENT/intent/history. Commands remain <=32 characters. PROFILE_ONLY identity.
See docs/MOVEMENT_0_3_5.md and exact update manifest. spawn_ready=false.

Cancellation runs only in a fresh server tick; its result is checked in a later
tick. No world access follows the native cancel call. STOPPED ends movement,
not lease cleanup: server ticks keep restoring owned hours after identity checks.
Cleanup status NONE/PENDING/DONE is reported separately. Identity loss, disk or
component failure leaves PENDING; no unsafe forced recovery or new move occurs.

Only after two seconds of decision5 outside Sleep/FindBed, under the owned
schedule override and an active Follow radius, wake.lua may queue ONE type1
NpcCommandEvent targeting this NPC's current position. No Reset/type0, raw
AI/decision/transform write or second event. It is a native navigation command,
not a teleport. No villager_move overlaps it. PID532656 confirmed that native
Roam/TargetReached is followed by Idle/Idle after the walker resets. Handoff now
accepts these consecutive ticks, at most1s apart, only with decision1, matching
target, proximity and previousState=Roam. An intervening state/target/decision
change discards the remembered arrival. Idle alone is not enough. The original
simultaneous Idle/TargetReached condition is also accepted. Timeout8s or error stops Follow and
restores the schedule. Type1's state transition was observed; the revised handoff and sustained Follow remain runtime unverified;
an uncertain event is never resent or forcibly cancelled. Native home/leash may
still interrupt later navigation. Neither static code nor simulated tests prove
successful wake or sustained Follow in game.

Runner stops at205s, hard Lua limit210s, heartbeat4s unchanged. Even reserving
15s for native wake plus8s for terminal handoff leaves182s of nominal observation.
Actual Follow duration must be measured; waiting for the player does not count.
