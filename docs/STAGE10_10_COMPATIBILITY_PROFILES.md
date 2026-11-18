# Stage 10.10 — compatibility profiles и evidence v7

Добавлены [1273043.json](../compatibility/profiles/1273043.json) и
[1287369.json](../compatibility/profiles/1287369.json), с индексом SHA-256
[index.json](../compatibility/profiles/index.json). Первый — `HISTORICAL_ONLY`,
второй — `CANDIDATE_BLOCKED_GAME_INTEGRITY`. Ни один не разрешает установку/spawn.

Профиль содержит version/build/EXE SHA, Steam identity где известна, EMF и EML
version/commit/digests, native/core API и Lua host version, Bridge protocol,
resource schema, source/custom GUID, npcId, metadata/fingerprints, gates,
runtime status и provenance. Приватные tokens и сохранения отсутствуют.

У нового профиля `observed_resource_metadata` хранит фактически прочитанные 82
компонента и fingerprint 5253f478 с `clean_baseline_verified=false`.
`expected_resource_metadata=null`: наблюдение изменённой базы нельзя превращать
в доверенный baseline. Поля старого profile не подставляются автоматически.

`load_profile(build)` требует точный файл, правильный SHA из index и совпадение
внутреннего game_build. Неизвестный build: `UNSUPPORTED_GAME_BUILD`, повреждённый
profile: `PROFILE_HASH_MISMATCH`, отсутствующий файл: `PROFILE_MISSING_OR_INVALID`.
Hash index обнаруживает несогласованное изменение, но не является криптографической
подписью автора. Согласованные изменения profile/index требуют code review.

`detect_build` проверяет EXE, при наличии — independent extracted metadata и
Steam build ID; несовпадение не компенсируется свежим логом. Actual rollback
helpers используют эту границу. Исторический installer и BodyClient mutation path
остаются закрыты для новой сборки. Архитектура Lua Body Adapter + Python Bridge
не заменялась.

Evidence **`aic_game_compatibility_evidence_v7`** реализована в
[compatibility.py](../companion/compatibility.py); опубликованный результат:
[evidence-v7.json](../compatibility/audits/1287369/evidence-v7.json).
14 обязательных sections: GAME_VERSION, GAME_FILE_INVENTORY, BACKUP_COMPATIBILITY,
EMF_COMPATIBILITY, EML_COMPATIBILITY, ECS_DIFF, RESOURCE_DIFF, CHARACTER_SETUP,
BRIDGE_COMPATIBILITY, PATCH_COMPATIBILITY, STAGE10_9_REVALIDATION, OFFLINE_TESTS,
INSTALL_READINESS, RUNTIME_STATUS. В каждой status, expected, observed, source,
provenance, identity, error, unknowns, runtime_validation_required.

Validator запрещает неподкреплённый PASS, отсутствие разделов/полей и повышение
Phase A до runtime/install/spawn success. UNKNOWN не считается PASS.
Исторические v3/v4/v5 evaluators сохранены; отдельный v6 в проекте ранее не был
реализован. Исторические evidence не редактировались.

Для следующего обновления: новый profile + исходные доказательства + полный
inventory и schema/resource diff; неизвестные поля остаются неизвестными.
После clean baseline — отдельный reviewed patch и collector, затем разрешения
Phase B/C. Один новый номер build в JSON не разрешает пройти gates.
