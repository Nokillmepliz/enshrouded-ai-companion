# Stage 10.10.2 — Animation Graph Compatibility Fix

**READY_FOR_PATCH_UPDATE_APPROVAL**, 2026-11-18.
Подготовка выполнена офлайн. Установленная версия остаётся0.5.0;
`runtime_validation=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`
относятся к новому кандидату0.5.1. Неудачный Phase F остаётся историческим результатом.

## Причина и доказательства

Ошибка объединённого assert не доказывала изменение animation graph. Найдена конкретная
несовместимость представления **пустого retargetData**: Inspector декодирует пустой GUID
как JSON null, а vendor EML передаёт Reference в Lua как строку, включая нулевой GUID.
Поэтому `retargetData == nil` не соответствует API для данного ObjectReference.

Использован чистый checkout EMF `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`,
совпадающий с ранее исследованной версией; новые загрузки или native builds не нужны.

- [value_to_lua, converter.rs:500–578](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/crates/mod-loader-lua/src/env/game/assets/value/converter.rs#L500):
  Guid и Reference → Lua String через GUID.to_string; Optional(None)/None → nil.
- [MappedStructValue::get_field](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/crates/mod-loader-lua/src/env/game/assets/value/mapped.rs#L160):
  контейнер поля — userdata; чтение поля вызывает этот converter. Сам GUID не является
  mapped/userdata объектом. Нет оснований принимать произвольные `.value`/`.guid` wrappers.
- [Value::from_guid](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/crates/kfc-resource/src/value/read.rs#L308):
  is_none GUID → Value::None при офлайн-декодировании; это объясняет JSON null.
- [Guid::NONE и Display](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/crates/kfc-base/src/guid/base.rs#L17):
  16 нулевых байтов, строковое представление `00000000-0000-0000-0000-000000000000`.
- Runtime-generated `.cache/lua/types.lua:3353–3355` объявляет оба поля
  AnimationGraphResourceComponent2 как ObjectReference. Кэш прочитан, не изменялся.
- Сохранённые актуальные decoded `hunter_assistant` и `blacksmith_assistant` содержат
  graph `402df515-5965-4b01-a17b-17d482a91af4`, retargetData=null.
  SHA-256 JSON: hunter `4c46c5d6a665f7c020724cb1f8c394da9b9961c633b03579bf5b8f1b529cba1d`,
  blacksmith `3532297d7899f6c3a82306831609be2f6b4445f8ad822def0060a5c4d1edf461`.
  JSON payload не публикуется. Итоговый повторный read-only аудит подтвердил прежние
  исходные KFC/resources/DAT, поэтому повторное декодирование базы не требовалось.

Старые fixtures использовали отсутствующее поле (Lua nil) и условные строки вроде
`graph`, что скрыло ошибку. Новый regression воспроизводит отказ0.5.0 на zero GUID.
Это установление ошибки по исходникам и fixture, а не захват фактического Lua-значения
в прошедшем запуске: старый log отдельных значений не содержал. Если фактический API
дистрибутива отличается от исследованного кода, новый patch выдаст отдельную диагностику.

## Изменения0.5.1

Исторические patch0.5.0, profile, пакет и receipt не менялись. Новая библиотека:
[`experimental/integrated_humanoid_0_5_1`](../experimental/integrated_humanoid_0_5_1/patch.lua).

- GUID: строгая строковая форма8-4-4-4-12 hex, нормализация регистра; неизвестные
  таблицы/userdata/числа/булевы значения не приводятся к строкам и отклоняются.
- Nullable: nil и подтверждённый zero GUID означают отсутствие; любой непустой
  retarget GUID при ожидаемом отсутствии — ошибка. Нулевой обязательный graph запрещён.
- Два поля проверяются независимо. До assert печатаются **обе** строки
  `AIC_GRAPH_DIAG_V1`: field/container type/Lua type/read method/actual/normalized/expected/result.
  Нет tostring неизвестного userdata или вызовов его методов. Строки ограничены и экранированы.
- Ошибки разделены на `ANIMATION_GRAPH_MISMATCH`, `ANIMATION_GRAPH_UNSUPPORTED_TYPE`,
  `RETARGET_DATA_MISMATCH`, `RETARGET_DATA_UNSUPPORTED_TYPE`.
  Если ошибочны оба поля, перечисляются оба кода. Диагностические строки не являются
  `AIC_EVIDENCE_V8`; parser не принимает их как завершённое evidence.
- Тот же строгий нормализатор применён к проверкам hierarchy GUID, visual reference
  GUID и lookup GUID. Подтверждённых дополнительных отличий типа этих полей не найдено.
  Компонентные/внешние/скелетные проверки, HashKey32, faction, GUID/npcId collisions,
  source/clone сравнения сохранены. Оригинальный шаблон не исправляется под ожидания.
- Evidence8 и Bridge protocol1 сохранены; Python валидирует явную версию0.5.1 из нового
  pinned binding. Legacy0.5.0 остаётся отдельным поддерживаемым контрактом, не fallback.
  CLI `integrated_observe.py --patch-0-5-1` требует выполненный новый receipt; его шаблон
  `TEMPLATE_NOT_EXECUTED` не позволяет подключение. Команды на этом этапе не отправлялись.

Новый [profile](../compatibility/updates/1287369/0.5.1/profile.json) существует отдельно
от исторического build profile, чтобы не нарушить pinned0.5.0 installation. Его SHA
привязан к плану, свежему run token и observer binding. Старый token не переиспользован.
Перед публикацией профиль приведён к LF, чтобы Git checkout не менял pinned SHA.
Первый CRLF-кандидат сохранён как superseded в project/runtime; финальный пакет
пересобран и повторно проверен на изолированной копии. Историческая установка не менялась.

## Shadow и fingerprint

[content_state.h:89](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_state.h#L89)
принимает как current только code0/unloaded/nontruncated/matching fingerprint.
[content_start.h:148–195](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_start.h#L148)
удерживает прошлую ошибку при том же fingerprint, но выбирает BuildHeld при его изменении.
Поэтому просто повторно запускать установленный0.5.0 бессмысленно.

[Fingerprint включает версию мода, имена, размеры, FILETIME](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_fingerprint.h#L62).
Предыдущий пересчитанный fingerprint совпал с реальным failed state:
`sha256:87af1e89d337ae475edc51dc7cdde6887ce20fc69c9befe94d7fc85addb7419e`.
Для подготовленного0.5.1, при сохранении указанных package FILETIME:
`sha256:17d1f36bb57e8dd9fc064eee5402ed4f10365d9970bda8fa975e7156638f1138`.
Это **проекция**, её надо пересчитать после разрешённого update. Fingerprint не заменяет SHA-256 файлов.

[Штатная подготовка shadow](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_shadow.h#L198)
удаляет имена private indexes/temps/generated DAT начиная с55 и каталоги cache/mod copies;
сохраняет правильные56 base hardlinks, копирует private indexes и новый mod.
Содержимое hardlinks не открывается на запись. Пустые root DAT055–063 не затрагиваются.
После успешного build нужен новый shadow.txt; старый failed state не доказывает успешного writer.

**Ручная очистка shadow/cache не требуется.** До разрешённого ручного запуска66 файлов
остаются на месте. Их [атрибуция с SHA/file IDs/link counts](../compatibility/updates/1287369/0.5.1/shadow-attribution.json)
сохранена для контроля; это не разрешение очистки. Безопасность штатной пересборки
обоснована закреплённым исходным кодом; фактическая пересборка0.5.1 ещё не выполнялась.

## Минимальный update и rollback

Пакет: `C:\Enshrouded-ai-companion\dist\stage10_10_2_patch_0_5_1`.
Все destination paths ниже относятся к `D:\SteamLibrary\steamapps\common\Enshrouded`.
[Exact update manifest](../compatibility/updates/1287369/0.5.1/update-manifest.json)
содержит current/new SHA-256, размеры, FILETIME, назначение, backup/restore policy для4 файлов:

1. `mods/aic_eml_humanoid/mod.json` — версия0.5.1.
2. `mods/aic_eml_humanoid/src/mod.lua` — patch, профиль и свежая привязка запуска.
3. `mods/aic_eml_humanoid/README.md` — соответствующая инструкция0.5.1.
4. `emf/mods/aic_integrated_observer/binding.lua` — новый run/plan/profile, без изменения observer0.3.0.

Все12 остальных installed files остаются прежними, включая DLL. Новой полной установки нет.
Старый receipt immutable, SHA `c3cd5da70e01fd073553b6dcc2598e8ede867693087b67c285d65253c59d70fc`.
Новый [receipt template](../compatibility/updates/1287369/0.5.1/update-receipt-template.json)
— честный `TEMPLATE_NOT_EXECUTED`, содержит parent SHA и effective16 hashes.
Фактический receipt может быть создан только после разрешённой проверенной транзакции.

[План дополнительного backup](../compatibility/updates/1287369/0.5.1/backup-plan.json):
**38 файлов /247154745 bytes (~247.2 MB; metadata дополнительно)**:4 заменяемых файла,
10 private shadow-файлов,23 актуальных LOCAL-файла и старый receipt. Hardlinks/55GB DAT
не копируются. Backup ещё не создан; старые backup/quarantine сохраняются. LOCAL backup
фиксирует текущие изменения шести файлов после Phase F, а не возвращает старое состояние.

Порядок после отдельного разрешения update:

1. Проверить закрытые game/server, build, pinned package/receipt/profile и все16 installed SHA.
2. Сравнить original67, LOCAL23 и shadow66 с опубликованным post-close snapshot; при любой
   неожиданной разнице остановиться, не исправлять manifest задним числом.
3. Создать новый backup по38 entries; повторно проверить SHA источников и копий.
4. Журналировать before/intent/verified для4 замен; проверять отсутствие reparse/hardlinks
   у каждого destination. Записывать временный private file, сверять SHA, затем заменять
   только разрешённый path; сохранять FILETIME package. При ошибке остановиться, без
   автоматического rollback и без выдачи успешного receipt при частичной транзакции.
5. Проверить16 effective hashes и fingerprint, original/LOCAL/shadow integrity; сформировать
   новый связанный receipt с backup SHA и журналом. Старый receipt не редактировать.
6. Выполнить file-restore dry-run по новому backup, остановиться перед игрой. Разрешение
   update не означает разрешение запуска или runtime validation.

[Rollback plan](../compatibility/updates/1287369/0.5.1/rollback-plan.json): восстановить4
старых файла только при совпадении текущих new hashes и проверенных backup hashes/mtime.
Не восстанавливать saves, не писать оригинальные ресурсы, не удалять shadow автоматически.
После следующего запуска потребуется новый аудит shadow; **full_live_rollback_ready=false**.
[Dry-run на изолированной копии](../compatibility/updates/1287369/0.5.1/rollback-fixture-result.json)
прошёл4 операции,16 effective hashes. Это не фактический rollback игры.

## Проверки и ограничения

- Python full suite **714 tests /713 PASS /1 existing skip /0 failures**,12.047s.
  Новых regression tests23; включая Lua fixtures в Lupa, ошибки типов/обоих assertions,
  stale state/version/fingerprint, родительский receipt, tampering, hardlink refusal,
  изолированное обновление/restore и запрет Bridge по template receipt.
- Lua syntax20/20 PASS (tracked Lua плюс новый patch и generated Lua); compileall PASS.
  Данные mapped-container fixture моделируются userdata, реальные GUID остаются строками;
  vendor DLL в тестах не исполнялась.
- [Decoded-source fixture](../compatibility/updates/1287369/0.5.1/decoded-fixture.json):
 82 components/63 dependencies/18 preset refs/102 joints, source unchanged, evidence8 roundtrip PASS
  с нулевой reference-строкой. Asset API/clone и scan замоканы; это не независимый collision
  scan, не сериализация EML и не подтверждение игрового рендера.
- [Повторный аудит](../compatibility/updates/1287369/0.5.1/integrity.json):222 game files и23
  LOCAL совпали с post-close snapshot по полным records (SHA/size/mtime/identity/links),
  включая66 shadow и16 installed; original67 неизменны. Clean backup27/27 повторно PASS.
  Новых изменений шести ранее изменившихся LOCAL-файлов нет. Game/server закрыты.

Ни игра, ни сервер, ни downloaded native components не запускались. EML/EMF не
переустанавливались, cache не очищался, saves не восстанавливались, NPC не создавались.
Возможны другие несовпадения вне graph-проверки, которые fixtures не покрывают;
фактическая0.5.1 сборка/serializer/writer/redirection/observer session/render ещё неизвестны.
Следующий шаг — получить разрешение на backup и четырёхфайловый update, после него
отдельно согласовать новый ручной load-only тест. Spawn остаётся запрещён.
