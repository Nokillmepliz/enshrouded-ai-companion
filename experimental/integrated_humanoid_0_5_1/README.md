# Integrated humanoid patch 0.5.1

EMF 0.6.18 integrated content, build 1287369 only. Generate `src/mod.lua`
with `scripts/prepare_patch_0_5_1.py`; never install the library alone.
The generated script contains the accepted baseline, dependency contract,
deployment identity and a fresh run token. No export capability is requested.

Creates one TemplateResource in the private content build, not an NPC. Preserves
CharacterSetup, animation, RenderEquipment and other component fields; changes
only clone name, faction enum and npcId. Unsupported reflection fails the build.
Evidence v8 print frames precede writer completion; they cannot prove successful
serialization, redirection, runtime rendering or safe spawning.

Vendor EML maps resource references to GUID strings, including the zero GUID
for an empty reference. Optional absence can be Lua nil. Graph and retarget
checks diagnose both fields before failing; unknown GUID userdata/tables are
rejected. AIC_GRAPH_DIAG_V1 lines are diagnostics, never completed evidence v8.
Historical patch 0.5.0 and its install receipt remain immutable.
No manual cache cleanup: the separately authorized next start uses EMF's native
shadow rebuild after the mod fingerprint changes. This package is not installed
until the user approves a four-file update and a new verified backup.
