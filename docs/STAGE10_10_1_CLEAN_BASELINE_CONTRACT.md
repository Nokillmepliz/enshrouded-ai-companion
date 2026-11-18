# Clean Baseline contract

Evaluator: `companion.recovery.clean_baseline`. Вход — отдельные `{status, source}` для build, recovery_source, fresh_inventory, official_resources, no_old_loaders, no_old_patch_observer, no_custom_clone, no_unknown_changes, no_guid_npc_collision, local_saves_intact. Caller обязан прикрепить реальные evidence, а не самостоятельно объявить PASS. Контракт не делает network/Steam/KFC lookup сам.

| Вердикт | Условие |
|---|---|
| CLEAN_BASELINE_FAILED | Хотя бы один FAIL: например старый loader/clone, collision, changed unknown EXE, изменённые saves |
| CLEAN_BASELINE_UNKNOWN | Нет подтверждённых проверок с provenance |
| CLEAN_BASELINE_PARTIAL | Часть PASS; либо всё локально проверено, но независимые depot hashes отсутствуют |
| CLEAN_BASELINE_CONFIRMED | Все десять PASS с источниками и independent_depot_hashes=true |

Fresh inventory и официальный depot manifest ID не равны официальным per-file hashes. Сейчас source database смешанная, независимого полного depot hash manifest нет. CONFIRMED **не получен**. Статический evaluator не поднимает readiness flags, даже на положительных fixtures.

При появлении нового build старый профиль не используется как fallback. Baseline identity должна включать полный список игровых ресурсов с SHA, EXE/build, Steam/depot, дату и источник проверки. Последующее изменение любого файла создаёт новый baseline; исторический receipt не переписывается.

Post-Steam audit состоит из fresh inventory + controlled Inspector output + attribution review + evaluator; одного скрипта, автоматически подтверждающего всё по сообщению Steam, намеренно нет. Отсутствующие данные остаются UNKNOWN.
