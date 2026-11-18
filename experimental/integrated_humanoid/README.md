# Integrated humanoid patch 0.5.0

EMF 0.6.18 integrated content, build 1287369 only. Generate `src/mod.lua`
with `scripts/prepare_phase_d_package.py`; never install the library alone.
The generated script contains the accepted baseline, dependency contract,
deployment identity and a fresh run token. No export capability is requested.

Creates one TemplateResource in the private content build, not an NPC. Preserves
CharacterSetup, animation, RenderEquipment and other component fields; changes
only clone name, faction enum and npcId. Unsupported reflection fails the build.
Evidence v8 print frames precede writer completion; they cannot prove successful
serialization, redirection, runtime rendering or safe spawning.
