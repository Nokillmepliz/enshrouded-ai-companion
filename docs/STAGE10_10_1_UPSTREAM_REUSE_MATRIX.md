# Матрица повторного использования

Состояние на закреплённом EMF0.6.18 source. `S`=CONFIRMED_BY_SOURCE, `P`=PARTIAL, `U`=UNAVAILABLE, `?`=UNKNOWN. Допустимые дополнительные статусы DOCUMENTED_ONLY и CONFIRMED_BY_UPSTREAM_RUNTIME_REPORT в этой таблице не используются: реклама и комментарий не заменяют аудит. `S` означает наличие реализации, не наш успешный игровой тест.

| Возможность | Наш проект | Companion | Beastmaster | Villager Jobs | EMF upstream |
|---|---|---|---|---|---|
| Humanoid body | P: clone, render UNKNOWN | U: default Vukah | U: звери | P: существующие villagers | P: templates/spawn |
| Custom template | P:0.4 historical/0.5 prep | P: GUID config | P: creature template configs | ?: custom clone | S: integrated EML |
| Spawn | S: закрытый Lua adapter | S: spawn | S: spawn | U: не создаёт тело | S: spawn/spawn_ex |
| Instance identity | P: fingerprint/guards | P: id/template/session | P: id/health/faction | P: npcId/place | U: public generation |
| Ownership | P: logical personality | P: sidecar | P: roster/account | P: job binding | U: atomic instance marker |
| Safe despawn | P: fail closed | P: destroy request | P: weak ours check | U: нет своего тела | P: destroy, без compare-instance |
| Follow | P: guard event | S: enemy guard/catch-up | S: animal guard/recall | U: jobs не follow | P: guard/villager primitives |
| Navigation | P: проектируется | P: native enemy AI | P: native animal AI | S: локальные jobs | S: path_find/villager_move |
| Ground query | P: safety gate | P: teleport ground | P: recall | P: recall | S: ground_at |
| Combat | U: не включён | S: enemy threat | S: beast modes | U: jobs | P: events/components |
| Inventory | U: не реализован | P: sidecar gear | U: нет humanoid inventory | P: chest job transfers | S: item transaction APIs |
| Equipment | U: visual неизвестен | P: level bonus | U: humanoid gear | U | P: component access; renderer unresolved |
| Persistence | P: personality отдельно | S: world sidecar | S: roster | S: jobs | P: engine villager policy |
| Reload recovery | S: блокировки/guard | S: session reset | S: roster reload | S: rebind jobs | P: session callbacks |
| Voice | U | U | U | U | U: companion voice stack |
| LLM integration | U | U | U | U | P: Bridge как транспорт |

Доказательства и ограничения по строкам: [Companion](STAGE10_10_1_COMPANION_RESEARCH.md), [Beastmaster](STAGE10_10_1_BEASTMASTER_RESEARCH.md), [Villager Jobs](STAGE10_10_1_VILLAGER_JOBS_RESEARCH.md), [native](STAGE10_10_1_NATIVE_EXTENSION_REVIEW.md). Строка inventory upstream означает существующие transfer APIs, не готовый собственный inventory у humanoid clone.

Происхождение/лицензии: все три мода в официальном EMF repo, MIT copyright2026 EMF contributors. При использовании существенного кода сохранять notices, pinned source/version, audit зависимостей. EML отдельно GPL-3.0; `emf_content.dll` GPL boundary, не MIT. Не публиковать чужие бинарники/игровые ресурсы. Новые файлы нашего проекта — самостоятельные контракты/тесты; upstream implementations сейчас не копировались.

Вердикт: **PARTIAL_UPSTREAM_REUSE**. Готовых частей стало больше, однако безопасный humanoid lifecycle, render и instance ownership не получены автоматически.
