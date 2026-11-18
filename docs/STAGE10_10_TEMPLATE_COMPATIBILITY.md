# Stage 10.10 — humanoid template и HashKey32

Read-only KFC Inspector повторно декодировал **64 ресурса** против текущего EXE:
два NPC templates, CharacterPresetCollection, ItemRegistryResource, hierarchy,
35 RenderModel и 24 связанных ItemInfo. 58 ресурсов равны прежним; изменены оба
templates, collection, registry и два hair ItemInfo. Raw dumps остаются в runtime,
публикуются только [метаданные сравнения](../compatibility/audits/1287369/resource-diff.json).

| Проверка | Наблюдение 1287369 |
|---|---|
| source GUID | `e3736dff-0ad2-47fc-903c-66c1775836e8`, найден |
| custom GUID | `a1c90001-5e4d-4a91-8a1c-000000000001`, **уже существует** |
| hunter / blacksmith / clone components | 82 / 82 / 82; раньше 81 |
| новый компонент | keen::ecs::GrassEffector |
| component fingerprint | **5253f478**, FNV32 sorted comma-separated type names |
| прежний fingerprint | 412d61b0; только для build 1273043 |
| source npcId / faction | 1633192162 / Player |
| clone npcId / faction | 2939921867 / PlayerAlly |
| animation graph | `402df515-5965-4b01-a17b-17d482a91af4`, прежний |
| retargetData | null, прежний |
| hunter preset | 1602195472, выбранная запись collection полностью совпала |
| visual references | прежние 18; выбранный preset и visual model links сохранены |
| RenderModel / hierarchy | 35/35 decoded и совпали; hierarchy тот же, 102 joints |
| source canonical SHA-256 | `58b9d7cb53d61b4d05b4e7eaf63a0b50109e086f322dbc4b8b3205d48a7a024d` |

Изменились `MovementColliderConfig.width`, `PathWalker.pushTowardsValidPosition`,
тайминги и reaction list в `ActiveNpcState.socializingSetup`. У двух hair ItemInfo
изменились generateKnowledge/overrideKnowledgeGeneration, а не visual model links.
Source и существующий clone различаются только template name, npcId и faction.
Это наблюдение сериализованной базы, **не новый controlled patch run**.

Визуальная цепочка source → preset → item → model → hierarchy доступна в текущей
базе. Это подтверждает наличие зависимостей, но не экранную модель, materials,
animation playback или поведение нового NPC. Полная чистота source и отсутствие
коллизии в чистом depot остаются неизвестны. npcId уже занят найденным clone;
полный поиск дополнительных npcId collisions по всем templates не выполнялся.

Девять значений совпали у source/clone и с историческими данными:

| Typed field | UInt32 |
|---|---:|
| voicePackId | 3178345104 |
| presetId | 1602195472 |
| hair | 100818570 |
| beard | 0 |
| hairColorId | 2593349132 |
| beardColorId | 2593349132 |
| skinColor | 510686028 |
| eyeBrowColor | 1294605571 |
| eyeColor | 1843389514 |

`gender=Male`, `useNewProportions=false`. EXE reflection подтверждает typed wrappers
и uint32 `.value`; EML source по-прежнему использует MappedStructValue.
Повторный runtime Lua reflection на 1287369 **не выполнен**. Python/Lua fixtures
не выдаются за это доказательство. Значения не вписаны обратно в игровые ресурсы.

Patch 0.4.0 нельзя объявить готовым для нового build: у него нет build/collision
guards, а evidence ссылается на исторический visual baseline. Подготовлен
[compatibility_guard.lua](../experimental/eml_humanoid_next/compatibility_guard.lua)
для будущего 0.5.0: подтверждённые `game.version`, `get_resource`,
`get_resources_by_type`, typed extraction, count/fingerprint, dependencies и npcId
collision scan. Это read-only библиотека без mod.json и без создания ресурсов.
Её проверки выполнены на Lua fixtures.

**Готового устанавливаемого patch 0.5.0 пока нет.** Причины: нет проверенного clean
baseline; own GUID присутствует; не выбран standalone/shadow content owner;
shadow loader выключает export, необходимый evidence. Эти блокеры нельзя устранить
подбором нового fingerprint. Историческая 0.4.0 и evidence v3/v4 сохранены.
Writer finalization, actual serialization и game resource lookup должны быть
заново проверены в отдельной Phase C после безопасной подготовки Phase B.
