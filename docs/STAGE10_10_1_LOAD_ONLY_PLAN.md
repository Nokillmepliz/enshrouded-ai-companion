# Будущая Phase F — load-only, без NPC

Этот сценарий подготовлен офлайн. Phase E/F не разрешены и не выполнялись.
Конкретные observer/Bridge команды будут зафиксированы после завершения Phase D;
несуществующий runtime API или готовый observer здесь не предполагаются.

1. Принятый clean baseline, verified clean backup, exact install manifest и новый
   rollback dry-run обязательны до отдельного согласования установки. Проверить
   Steam/internal build, absence legacy loaders/mods/configs и один content owner.
2. После разрешённой установки проверить receipt и каждый destination SHA, создать
   новый run identity. Legacy receipt1273043/patch0.4 не использовать.
3. До запуска снять original EXE/KFC/resources/DAT identities/SHA/link count и LOCAL
   inventory. Проверить, что оригиналы ещё не имеют неизвестных hardlinks и `.bak`
   не может подменить выбранный clean source. Включить только patch/readonly observer.
4. Игру запускает пользователь. Body Test / AI Body Test — LOCAL slot1 только после
   проверки соответствия актуальным saves. Их работоспособность/отсутствие миграции
   в build1287369 ещё не проверены. При риске миграции предложить новый изолированный
   тестовый LOCAL character/world; не править существующие saves инструментами.
5. После сообщения «загрузился» read-only capture: EMF/core/Lua/observer versions,
   protocol1, actual LOCAL/session/world, receipt/run match. Смену мира/сессии,
   missing identity или stale evidence считать отказом.
6. Из content.log получить полный v8 BEGIN/END frame set: source/clone typed fields,
   fingerprints, preset/graph/18 refs/skeleton/RenderEquipment по новому clean контракту,
   resource registration/lookup и source integrity. Числа18/102/82 не подставлять
   автоматически, если fresh clean inspection даст другие значения.
7. Независимо проверить writer completion, content DLL unload, state fingerprint,
   shadow.txt, resource redirection. DLL выгружена — её EML resource API нельзя
   вызывать из runtime observer. Нужен offline Inspector finalized shadow readback,
   связанный с этим build/run, и отдельная свежая runtime session.
8. Проверить shadow filesystem validator и неизменность original hashes;
   synthetic fixture PASS не засчитывать. Сопоставить A/H/R/V/B/C с original resource,
   single owner, shadow, writer, freshness, redirect и observer gates. Ошибка/unknown
   остаётся ошибкой/unknown; render не подтверждается одним resource lookup.
9. Пользователь закрывает игру. Повторить original/DAT/installed hashes, link identities,
   LOCAL inventory, ADDED/REMOVED/CHANGED и атрибуцию новых shadow artifacts.
   Нормальную запись saves самой игрой документировать, не стирать и не восстанавливать
   автоматически. При неожиданной mutation оригиналов прекратить дальнейшие действия.
10. Опубликовать sanitized evidence/verdict. Rollback только по отдельному разрешению.

Не выполнять spawn/despawn, faction/inventory/entity mutations. Даже при успешном
load-only: `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
