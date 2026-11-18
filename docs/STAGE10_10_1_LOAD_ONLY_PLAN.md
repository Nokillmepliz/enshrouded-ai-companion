# Будущая Phase F — load-only, без NPC

Этот сценарий подготовлен офлайн. Phase E/F не разрешены и не выполнялись.
Офлайн-Phase D завершена: [пакет и hashes](STAGE10_10_1_PHASE_D_REPORT.md).
Следующие команды предназначены только для отдельно разрешённой Phase F после
успешной Phase E и ручного запуска пользователем; сейчас их не выполнять.

1. Принятый clean baseline, verified clean backup, exact install manifest и новый
   rollback dry-run обязательны до отдельного согласования установки. Проверить
   Steam/internal build, absence legacy loaders/mods/configs и один content owner.
2. После разрешённой установки проверить receipt и каждый destination SHA, создать
   deployment run identity из проверенного пакета. Для каждого запуска фиксируется
   также новый process/session token и окно времени; receipt1273043/patch0.4 не использовать.
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

## Подготовленные команды

Из `C:\Enshrouded-ai-companion`, только после разрешения Phase F:

```powershell
.\.tools\python\python.exe scripts/integrated_observe.py status --package dist/stage10_10_1_phase_d_20261118 --game 'D:\SteamLibrary\steamapps\common\Enshrouded' --receipt '<новый Phase E receipt.json>' --receipt-sha256 '<SHA из отчёта Phase E>' --live-read-only
```

Для build evidence заменить `status` на `inspect`, затем `compare`. Placeholder
receipt обязателен: настоящий файл появится только после Phase E. Клиент проверяет
package, pinned plan/binding, receipt и installed hashes до подключения. Доступны
только три перечисленные команды; произвольный console/spawn не поддерживается.
Не перенаправлять вывод в game или saves. Private session/run в журнале не публиковать.

`ok=true` здесь означает принятую read-only команду и проверенные session/build
observations. Итоговый evaluator по умолчанию возвращает LOAD_ONLY_UNCONFIRMED:
writer/shadow/readback/redirect нужно независимо приложить как `{status,source}`.
Нельзя заполнять эти gates значением PASS только по ответу observer.

До ручного запуска сохранить original snapshot через
`companion.shadow_integrity.capture_originals`, current LOCAL inventory и
`companion.integrated_writer.content_fingerprint(game)` после installed hash checks.
Зафиксировать время до запуска, затем actual process start и session token.
После загрузки `validate_state` проверяет content state в этом свежем временном окне.
Cached evidence прежнего запуска не подтверждает свежую writer execution.

Фактический finalized shadow исследовать тем же pinned read-only KFC Inspector:
clone/source lookup и component fields, resource containers/contents, dependency
GUID/type, collision/registration и неизменность source. Ожидаемые shadow hashes
утвердить на основе этого readback, не автоматически брать из неизвестной папки.
`audit_shadow(..., base_dat_count=55)` проверяет EXE/55 DAT links, private outputs,
девять сохранённых root DAT и оригиналы. Свежий `file_opens.log` должен отдельно
подтвердить реальные открытия redirected KFC/resources/DAT текущим процессом.

После закрытия игры повторить installed/original/LOCAL inventory. Новые save writes
самой игры документируются; резервная копия автоматически не восстанавливается.
Rollback после runtime shadow требует нового attributed artifact manifest и
отдельного разрешения. Никакое состояние load-only не разрешает spawn.
