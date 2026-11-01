# Stage 10.9 — проект template variants

Оба варианта существуют только как проект. Текущий проверенный Stage 10.7 template, GUID `a1c90001-5e4d-4a91-8a1c-000000000001` и patch 0.4.0 не изменены. Окончательные GUID/npcId не назначены до offline collision scan по KFC/EML registry и отдельного load-only теста.

| Свойство | `aic_humanoid_visual_test` | `aic_humanoid_companion` |
|---|---|---|
| Назначение | один временный visual experiment | будущий постоянный companion |
| CharacterSetup/visuals | копия подтверждённого source | копия подтверждённого source |
| Animation graph | сохранить `402df515-5965-4b01-a17b-17d482a91af4` | сохранить |
| Faction | PlayerAlly (11), runtime verify | PlayerAlly (11), runtime verify |
| ForceSave | удалить-кандидат | сохранить-кандидат после lifecycle research |
| ActiveNpcState | удалить-кандидат | отдельный collision-free npcId |
| ActiveNpcStateSaved | удалить-кандидат | сохранить-кандидат |
| DoNotSave | добавить-кандидат | не добавлять |
| Unique NPC lifecycle | должен отсутствовать | должен быть полностью управляемым |
| Статус | DESIGN_ONLY | DESIGN_ONLY |

Component diff нельзя применять вслепую. Для visual variant нужно статически проверить зависимости всех 81 компонентов и EML serialization, затем load-only lookup. Удаление `ActiveNpcState` может отключить villager initialization/animation behavior; добавление `DoNotSave` ещё не доказано для custom villager. Render closure по Stage 10.7 сохраняется без изменений, но реальный render всё равно требует отдельного spawn-теста.

Для permanent variant нужно доказать NpcRegistry registration, uniqueness key, KSD representation, reload identity, duplicate suppression и targeted removal. Один новый GUID/npcId снижает collision risk, но не является instance identity.

Ни один variant сейчас не готов к установке или spawn.
