# Stage10.10.3 — Bridge Access & Runtime Validation

## Текущий результат: runtime PASS, ожидается ручное закрытие

2026-11-18, запуск пользователем в 17:15:49 MSK, PID 202212.
Адресная диагностика вне sandbox через штатное согласование прошла успешно:
SID клиента и игры совпадают, integrity достаточен, security descriptor pipe прочитан.
Права и настройки безопасности не менялись. Bridge hello/state PASS:
EMF 0.6.18 / API 46 / protocol 1 / build 1287369.

LOCAL Body Test slot 1 / AI Body Test slot 1 подтверждены Bridge до и после
observer compare. Compare и завершающий status прошли nonce, binding/profile,
session identity и read-only проверки; evidence v8 содержит все 40 проверенных полей.
Активны только Lua 1.39.0 и observer 0.3.0. Новых команд мутации не выполнялось.

Loader сообщает повторное использование успешного cache 0.5.1 от 13:46:15 UTC.
State побайтно совпадает с preflight: прежний fingerprint, code 0, unloaded=true,
нет warnings/errors. Это повторное использование сборки, а не свежий writer run.
Ранее выполненный независимый readback не повторялся; его применимость окончательно
проверим полным post-close контролем shadow. Свежий file-open log этой сессии
подтверждает 66 успешных перенаправленных открытий KFC/resources/DAT для чтения;
фактические ReadFile bytes и отображение модели этим не доказаны.

В разовом офлайн-сводном вызове допущена опечатка имени `enshrouded.kfc.resources`.
Она вызвала INCOMPLETE; после сверки с существующим контрактом использовано правильное
`enshrouded.kfc_resources` на том же сохранённом логе: PASS 66/66. Валидатор не ослаблялся,
дополнительных обращений к Bridge или игровых действий для исправления не выполнялось.

[Публичный checkpoint](../compatibility/updates/1287369/0.5.1/stage10_10_3/load-only/runtime-checkpoint.json)
содержит хеши private evidence без SID, run token и сырых логов.
Итог пока `LOAD_ONLY_UNCONFIRMED_UNTIL_POST_CLOSE_AUDIT`:
необходимо ручное закрытие и post-close audit v2 оригиналов, 16 installed files,
77 shadow files и LOCAL saves относительно текущего preflight.
`spawn_ready=false`, `runtime_render=UNKNOWN`. Игра запущена пользователем;
установка, ACL, cache, shadow и сохранения агентом не изменялись, rollback не выполнялся.

## Продолжение: fresh preflight 2026-11-18,14:12:27 UTC

Пользователь отдельно разрешил завершение load-only и адресную read-only диагностику
вне ограниченного sandbox через штатное согласование. **READY_FOR_MANUAL_START**.
Игра и сервер закрыты. Build, pinned package/profile/binding/receipt, installed16/16,
verified backup38/38 и clean backup27/27 проверены заново. File-only rollback dry-run4
PASS; откат не выполнялся и не разрешён.

Полный snapshot234 game/23 LOCAL точно равен актуальному reviewed post-close baseline,
включая67 originals и77 shadow; SHA/size/identity/mtime/links совпали. Fingerprint0.5.1
прежний. При неизменных ресурсах независимый Inspector readback повторно не запускался.
LOCAL character0/world0 подтверждены актуальными SHA и именами Body Test / AI Body Test;
runtime name/storage/slot будут проверены через Bridge после загрузки.

Private checkpoint: `runtime/stage10_10_3/load_only/20261118T141227374049Z`.
[Новый preflight](../compatibility/updates/1287369/0.5.1/stage10_10_3/load-only/preflight.json).
SHA baseline/inventory: `9bb5ef6895915469d1e35a302b2071f2037348049f4f07e0178c39a3237ae904`.
Существующий preflight получил явный режим `--stage10-10-3` с pinned актуальным
baseline; старые checkpoint не перезаписываются. Py_compile/diff check PASS,
реальное выполнение exit0; полный unit suite здесь повторно не запускался.

Следующий шаг: пользователь вручную запускает LOCAL Body Test / AI Body Test (slot1)
и сообщает «загрузился». Codex определяет новый PID и адресно выполняет подготовленный
diagnostic, затем observer compare через штатный approved invocation. При невозможности
такого выполнения предоставляется готовая команда для обычного PowerShell пользователя.
Права/моды не меняются. Успешный cache0.5.1 сохранён: повторная сборка не обязательна,
нужно связать его проверенные хеши с текущей сессией и новыми redirect/Bridge наблюдениями.
После ручного закрытия — post-close audit v2 и итоговая публикация.
`runtime_validation=WAITING_FOR_MANUAL_START`, `spawn_ready=false`, render UNKNOWN.

## История офлайн-этапа

2026-11-18. Офлайн-разработка и read-only диагностика после load-only0.5.1.
Исходный commit `06186275a5247bc5f5e4fd2508315615897a8eab`;
исторические BLOCKED-результаты Stage10.10.2 сохранены без изменений.

## Bridge: установлен механизм отказа, нужна проверка живого процесса

Текущий Python запущен sandbox от **codexsandboxoffline**, с restricted token,
Medium integrity (`S-1-16-8192`), без elevation и AppContainer. Это подтверждено
`whoami` и `OpenProcessToken/GetTokenInformation`; private результат:
`runtime/stage10_10_3/current-context.json`. WMI-запрос владельца explorer из sandbox
также получил access denied. Права не менялись, запрос не повторялся с повышением.

Закреплённый EMF commit `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241` задаёт pipe:

- Protected DACL: deny Network, allow только SID пользователя процесса игры и SYSTEM.
- Mandatory label `NWNR` на integrity level игры; клиент ниже этого уровня запрещён.
- `PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED`, byte mode, remote clients rejected.
- После подключения дополнительно проверяются PID, равенство user SID и достаточный
  integrity level клиента. Несовместимый token не исправляется изменением протокола.

Доказательства в исходниках:
[SDDL и client identity](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/bridge/pipe_server.cpp#L53),
[CreateNamedPipe](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/bridge/pipe_server.cpp#L154).
Лог сессии подтверждает включение `emf-bridge-187928` в16:46:18, «this Windows user only».

**Sandbox затронут:** он использует отдельную учётную запись, которую стандартная
DACL пользовательской игры не допускает. Это объясняет наблюдённый error5.
Но SID/token и фактический security descriptor процесса187928 во время ошибки
не были сняты, а процесс уже закрыт. Поэтому точная историческая причина остаётся
**наиболее обоснованной гипотезой, не окончательно измеренным диагнозом**.
Дополнительное влияние integrity/ACL не исключено. Данные про8 клиентов отсутствуют.

Клиент использует `CreateFileW(GENERIC_READ|GENERIC_WRITE, OPEN_EXISTING,
SECURITY_SQOS_PRESENT|SECURITY_IDENTIFICATION)` — без impersonation.
[Закреплённый Python client](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/tools/bridge/emf_bridge.py#L327).
Сравнение нашего vendored client с этим commit выявило только одну изменённую
текстовую подсказку `load_world` о поддерживаемом build. Транспорт/доступ/protocol1
совпадают. **Замена протокола или native EMF не требуется.** Vendored файл не изменён.

В wrapper добавлена классификация:5 ACCESS_DENIED,2/3 PIPE_NOT_FOUND,
231 PIPE_BUSY,121 WAIT_TIMEOUT,109 PIPE_BROKEN,233 PIPE_DISCONNECTED.
Занятый pipe не доказывает8 активных клиентов. Для error5 сообщение теперь предлагает
проверить SID/integrity/sandbox, а не повторять предположение о лимите.

## Post-close validator v2

Архив `backup/enshrouded_2026-11-18T16-46-15.log` **полностью совпадает** с прежним
`enshrouded.log`: SHA, размер, volume/file ID,mtime,links1. Новый текущий лог имеет
другой file ID. Это переименование при ротации, не произвольный новый файл.
Архив начинается прежней сессией12:35:08 UTC; новый file_opens log показывает
открытие нового `enshrouded.log` с CREATE_ALWAYS при старте16:46:15.
CopyFile/MoveFile вызовы не перехватываются этим логгером: происхождение доказано
совпадением файла и его identity в before/after snapshots, а не выдуманной строкой MoveFile.
Исходники закрытой игры недоступны; исходники EMF этого действия не приписывают себе.

`emf/chain_status.txt`: пустой файл, SHA `e3b0c442…b855`, тот же file ID/volume/links1,
изменился только mtime в пределах запуска. EMF открывает его в `wb` при каждом старте:
[dllmain.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/dllmain.cpp#L157),
[формирование пустого status при отсутствии chain](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/chain_load.h#L60).

Новый `reassess_post_close` разрешает только конкретный reviewed архив с совпадающей
identity старого лога и такой metadata-only update пустого chain_status. Изменённый SHA,
новый file ID chain_status, hardlinks, mtime вне сессии, неизвестные backup/emf файлы
и удаления отвергаются. Original/installed/shadow проверки выполняются отдельно и
не ослаблены. Результат v2 публикуется отдельно от исторического POST_CLOSE_BLOCKED.

## Независимый readback

Использован существующий `.tools/kfc-inspector/target/release/kfc-readonly-inspect.exe`,
SHA-256 `81531333e5b73d7c1fed55dcfb8284c874deb2e4f84a6a68dbe4bed79314f075`.
DLL/EXE и patch не пересобирались. Открывались текущие shadow KFC/resources/DAT,
оригинальный source template, hierarchy и preset collection. Декодированные ресурсы
сохранены только в `runtime/stage10_10_3/decoded`, не публикуются.

- Clone GUID `a1c90001-5e4d-4a91-8a1c-000000000001`, npcId2939921867, PlayerAlly.
- Полное глубокое сравнение всех82 компонентов и всех top-level полей с исходным
  template: разрешены ровно3 изменения — name, Faction.faction, ActiveNpcState.npcId.
- Source в shadow полностью равен source из original KFC; canonical SHA совпадает
  с закреплённым profile. Непредусмотренных изменений исходного шаблона нет.
- CharacterSetup целиком совпал:9 HashKey32, gender/proportions. AnimationGraph и
  nullable retarget совпали; RenderEquipment сохранён по всем значениям.
- Hierarchy102 joints и вся preset collection совпали с prior clean decoded baseline.
 18 visual references выбранного preset проверены независимо от evidence v8.
-63 typed dependencies разрешены по composite identity `(GUID,type,part=0)`.
  Один GUID может иметь несколько resource types (например ItemInfo и UiTexture);
  это не дубликат composite identity. Неверный тип/part и duplicate identity запрещены.
- Независимый database audit:12270 templates декодированы,91910 resource-index rows,
 101492 content references,59 resource chunks; duplicate IDs0. Ровно один template
  соответствует npcId — наш clone.
-9 private DAT055–063 **пустые**:0 bytes/entries. Само их наличие не доказывает
  создание визуального содержимого. Шаблон независимо прочитан из shadow базы.

Проверяется точный shadow set77:56 base hardlinks,3 private indexes,9 DAT,
3 mod copies,4 cache-файла,2 metadata. Использован существующий `audit_shadow` с
первоначальным single-link original baseline; источник не подменяется текущим shadow.
Private output hashes фиксируют фактическую сборку после семантического readback и
database bounds checks, не являются заранее известными release hashes всей базы.
Shadow manifest сверяется с исходными EXE/KFC/resources size+FILETIME/dat_count64;
state/fingerprint проверяются существующим validate_state.

## Resource redirection

Сохранённый file_opens.log относится к16:46:15 и `redirect_test=1`.
Найдено успешное `CreateFileA/W` с GENERIC_READ, OPEN_EXISTING и корректным handle
для **всех66 ресурсов: KFC, resources и DAT000–063**, с исходным путём из game root
и целевым путём в `emf/content/client`. Ошибки, write-only операции, metadata lookup,
чужой shadow path и stale session не считаются подтверждением.

[Реальный hook](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/file_hooks.h#L203)
вызывает настоящий CreateFile по выбранному target и логирует возвращённый handle.
Таким образом подтверждены генерация, настройка redirect и **фактические успешные
открытия игрой для чтения**. ReadFile/ReadFileEx и объёмы прочитанных байтов не
трассируются; отображение модели из этого evidence не следует.

## Минимальный следующий runtime-план — только после отдельного разрешения

1. Свежий read-only preflight по актуальному post-close baseline234/LOCAL23.
   Не использовать snapshot до последнего запуска:7 LOCAL-файлов уже изменились.
2. Пользователь вручную запускает игру и LOCAL Body Test / AI Body Test.
3. В обычном PowerShell **того же пользователя, что запустил игру**, без «Запуск от
   администратора», выполнить подготовленный diagnostic. Он читает token/ACL, затем
   только hello/state; при несовпадении SID/integrity или отказе останавливается.

```powershell
Set-Location C:\Enshrouded-ai-companion
$gamePid = (Get-Process -Name enshrouded -ErrorAction Stop).Id
.\.tools\python\python.exe scripts/diagnose_bridge_access.py --pid $gamePid --live-read-only --output runtime/stage10_10_3/live-user-context-01.json
```

Имя output должно быть новым. `187928` повторно использовать нельзя.
Диагностический файл содержит SID/context и остаётся private. Если pipe security
descriptor недоступен, программа фиксирует отказ и не отправляет protocol requests.
Ни ACL, ни UAC, ни антивирус, ни настройки sandbox не меняются.

Альтернатива — отдельный адресный approved tool invocation вне ограниченного
контекста для этой диагностики после явного разрешения пользователя; это не отключение
sandbox целиком. В Stage10.10.3 такая live-попытка **не выполнялась**.

4. При успешной диагностике проверить результат и выполнить существующий
   `integrated_observe.py compare --patch-0-5-1 --live-read-only` с pinned package/receipt
   из Stage10.10.2. Он проверяет LOCAL slot/name/storage и observer session без мутаций.
5. Пользователь закрывает игру; повторить post-close audit v2. При ошибке остановиться.

Даже после успешного load-only первый spawn требует отдельного согласования и
проверки ранее подготовленного safety/lifecycle плана. Этот этап spawn не разрешает.

## Проверки и итог

29 новых regression tests: error classification, точная ротация/metadata attribution,
запрет неожиданных изменений, full clone/source semantics, dependency identity,
visual references и redirection. Full suite **758 testsRun /757 PASS /1 skip /0 failures**,
16.179s. Compileall companion/scripts/tests и git diff check PASS. Прежний skip сохранён.
Private log: `runtime/stage10_10_3/tests.log`.

Полный результат офлайн-аудита:
[stage10_10_3/result.json](../compatibility/updates/1287369/0.5.1/stage10_10_3/result.json).
Фактический финальный audit14:05:36 UTC: original67, installed16, backup38 и shadow77
PASS. До и после исследования SHA/size/identity/mtime/links всех234 game records и23
актуальных LOCAL records совпали. SHA полного before/after snapshot одинаков:
`9bb5ef6895915469d1e35a302b2071f2037348049f4f07e0178c39a3237ae904`.
Дополнительные backup не создавались. История/quarantine сохранены.

Итоговые критерии: A/H/R/C PASS, V REFERENCES_ONLY, B UNKNOWN. Пересмотр v2 устранил
UNATTRIBUTED_NON_SHADOW_CHANGES для этой сессии; исторический v1 BLOCKED остаётся.

**LOAD_ONLY_UNCONFIRMED** до измеренного успешного observer/Bridge runtime context.
Причина error5 сужена до контекста безопасности; live token/ACL старого процесса
неизвестны. `spawn_ready=false`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`.
Игра/сервер не запускались, установленный payload, права, shadow/cache и сохранения
агентом не изменялись; rollback не выполнялся. После публикации — остановка.
