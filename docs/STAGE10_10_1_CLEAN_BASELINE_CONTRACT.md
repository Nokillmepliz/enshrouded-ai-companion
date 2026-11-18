# Clean Baseline contract

Evaluator: `companion.recovery.clean_baseline`. Вход — отдельные `{status, source}` для build, recovery_source, fresh_inventory, official_resources, no_old_loaders, no_old_patch_observer, no_custom_clone, no_unknown_changes, no_guid_npc_collision, local_saves_intact. Caller обязан прикрепить реальные evidence, а не самостоятельно объявить PASS. Контракт не делает network/Steam/KFC lookup сам.

| Вердикт | Условие |
|---|---|
| CLEAN_BASELINE_FAILED | Хотя бы один FAIL: например старый loader/clone, collision, changed unknown EXE, изменённые saves |
| CLEAN_BASELINE_UNKNOWN | Нет подтверждённых проверок с provenance |
| CLEAN_BASELINE_PARTIAL | Часть PASS; либо всё локально проверено, но независимые depot hashes отсутствуют |
| CLEAN_BASELINE_CONFIRMED | Все десять PASS с источниками и independent_depot_hashes=true |

Fresh inventory и официальный depot manifest ID не равны аутентифицированным upstream per-file hashes. После ручного Steam Verify получен новый [post-Steam audit](STAGE10_10_1_POST_STEAM_AUDIT.md): KFC55 containers, старый clone отсутствует,61/61 depot entries совпали с plaintext cache manifest. Его signature section пустой, независимая аутентификация отсутствует. CONFIRMED **не получен**, фактический verdict PARTIAL. Прежняя смешанная database сохранена только в historical evidence/backup/quarantine. Статический evaluator не поднимает readiness flags, даже на положительных fixtures.

Ограниченное принятие PARTIAL согласовано пользователем 2026-11-18 по разделу12 ТЗ Phase C/D. Оно не меняет verdict на CONFIRMED, не подделывает `independent_depot_hashes` и не разрешает установку. Scope — verified clean backup и офлайн-Phase D; дополнительная независимая аутентификация не требуется. [Acceptance и backup](../compatibility/recovery/1287369/post_steam/accepted-backup.json), [готовый пакет](STAGE10_10_1_PHASE_D_REPORT.md). На предыдущем post-Steam checkpoint это было только предложением; новая запись отражает полученное позднее согласие.

При появлении нового build старый профиль не используется как fallback. Baseline identity должна включать полный список игровых ресурсов с SHA, EXE/build, Steam/depot, дату и источник проверки. Последующее изменение любого файла создаёт новый baseline; исторический receipt не переписывается.

Post-Steam audit состоит из fresh inventory + controlled Inspector output + attribution review + evaluator; одного скрипта, автоматически подтверждающего всё по сообщению Steam, намеренно нет. Отсутствующие данные остаются UNKNOWN.
