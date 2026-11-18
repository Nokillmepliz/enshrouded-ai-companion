# Evidence без export; patch/observer preparation

Подтверждён исходниками путь **EML print → tracing callback → emf/content.log**: [env/log.rs](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/crates/mod-loader-lua/src/env/log.rs#L5), [callback/build](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/content/src/lib.rs#L90). `RunOptions.export=false` на строке316. `io.open` в EMF Lua разрешён; это другой Lua environment, не основание выдумать запись файла в EML sandbox.

Подготовлены offline `experimental/eml_humanoid_next/evidence_log.lua`, `experimental/observer_next/observer.lua`, `companion/migration_observer.py`. **Это библиотеки подготовки без mod.json/bootstrap/install plan, не установленный и не runtime-проверенный observer.** Старые patch0.4/observer/BodyClient не заменены. Нет подключения к pipe, открытия bridge или entity API. `status/inspect/compare` регистрируются только через подтверждённые `emf.command/reply`; остальные команды controller отвергает.

Проектный framing (не EMF API): `AIC_EVIDENCE_V8|<build-run-token>|<key>|<value>`. 11 полей и завершающий count; <=4096 bytes/line; duplicate/stale/truncated/malformed/type-mismatch → отказ. Typed HashKey32 сериализуются девятью uint32, boolean не считается числом. Lua emitter валидирует все строки до первой отправки. JSON/строковые значения формируются из typed reads, не из скопированных констант.

| Доказательство | Будущий источник |
|---|---|
| Patch/source/clone/CharacterSetup/nine HashKey32 | Guard + typed EML reads до/после регистрации, structured frames |
| Component fingerprint, graph, references, lookup | Полный EML readback + external read-only Inspector shadow output |
| Writer finalized | Content build success, корректный state/shadow.txt, unloading success, повторный lookup на finalized shadow |
| Build/exe/receipt/file identity | Preflight/install receipt и fresh hashes |
| Runtime session/world | Отдельная current Bridge/observer capture после загрузки LOCAL world |
| Render/behaviour | Только отдельное разрешённое игровое испытание; сейчас UNKNOWN |

Patch executes до появления runtime world, поэтому `server_session` нельзя выдумать внутри EML. Build token связывает patch/log/state, а session/world связываются позднее в capture. Кешированный build может не печатать новые строки: принимается только matched build artifact с verified fingerprint и отдельной свежей session binding; отсутствие привязки блокирует. Для принудительно нового build token потребуется отдельно разрешённое обновление patch/config до запуска, не запись во время read-only диагностики.

`content.log` обнуляется при build. Хранить копию в project evidence после чтения, проверять complete frames и digest; не смешивать старый exportv4 с новым v8. Print после create_resource ещё не доказывает final writer close. Отсутствие ошибок и одиночное `built` без readback недостаточны.

Bridge wire остаётся protocol1: [protocol.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/bridge/protocol.h#L16). API20→46 расширяет native ABI, не делает старый build profile совместимым автоматически. Старый BodyClient mutation preflight остаётся закрытым. Новый validator диагностирует build/API/EMF/Lua-host/protocol/session/world/owner/patch/receipt/run mismatch, missing evidence, writer/readback, baseline mismatch. Capture callback и доверенный evidence baseline ещё нужно реализовать/сформировать в Phase D на чистой базе; библиотека не выдаёт supplied fixture за live capture.

Patch0.5: **PATCH_PREPARATION_ONLY**. Сохранены исторический0.4, sourceGUID `e3736dff-0ad2-47fc-903c-66c1775836e8`, cloneGUID `a1c90001-5e4d-4a91-8a1c-000000000001`, graph/visuals/typed reads. Существующий compatibility_guard должен предварять единственную регистрацию, collision scan и source-unchanged comparison. Наблюдавшиеся82 components — факт смешанной базы, не искусственная норма нового patch. Доверенный список/fingerprint получаем после Phase C; финальный patch не собран.

Все offline-ответы оставляют `runtime_status=NOT_EXECUTED`, `spawn_ready=false`; evidencev8 не подменяет исторический v7.
