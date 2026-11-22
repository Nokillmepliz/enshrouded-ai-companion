# Companion Movement 0.2.1 — Stage 10.13

Registration fix: f_start/f_step/f_stop/f_status, fully qualified names <=32.
Registration failure fails mod load. Existing follow-session.lock is preserved.
Python continuation appends once to the SAME journal only after a pinned audit
proves the previous command was unregistered and the session never started.

Offline Follow Prototype. No automatic start on mod load. Separate installation
and runtime approval required. Only LOCAL Body Test / AI Body Test, unique NPC
profile; PROFILE_ONLY identity, no persistent GUID proof.

Python Runner validates Bridge/context before and after each request. One durable
journal and follow-session.lock permit one session. Previous SPENT/spawn/movement
intents are never reset. Legacy move_to is disabled.

Limits: 180 seconds, 24 orders, two recovery attempts, polling at most once per
second, four-second command cooldown. Enter radius 19 m, exit >20 m. Target 1.8 m
from player towards NPC; bounded recovery rotates it. Ground/Wall/Path, freshness,
unique identity and no foreign order required. Native villager_move enforces
home/leash. No teleport, component writes, persistence or direct save access.

follow_config.lua roaming='native' preserves wandering (current package).
roaming='hold' requests a finite five-second native hold after arrival. This
returns NPC to the point, does NOT disable its AI. Far away: no new orders; cancel
our current order. Full roaming suppression compatible with movement remains
unconfirmed. Change the switch only in a reviewed package with the game closed.

Four-second heartbeat watchdog stops the session. Lost identity forbids cancel;
orders remain bounded to 12 seconds, optional hold to five. STUCK is not ARRIVED.
See docs/STAGE10_13.md in the project repository.
