# Stage 10.10.1 — завершение офлайн-Phase D, 2026-11-18

Последующее событие: пользователь разрешил Phase E, установка завершена.
[Актуальный отчёт Phase E](STAGE10_10_1_PHASE_E_REPORT.md). Ниже сохранено состояние
пакета на завершение Phase D; исходный approved manifest не переписывался.

**MIGRATION_PACKAGE_READY / READY_FOR_PHASE_E_APPROVAL.** Пользователь принял
`CLEAN_BASELINE_PARTIAL` с ограничением доверия к локальному Steam depot manifest.
Независимая аутентификация не выполнялась повторно. Формальный baseline остаётся
PARTIAL; это отдельное, явно принятое ограничение, а не доказанная подпись Valve.

`installation_authorized=false`, `installation_executed=false`,
`runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
Игра/server/EMF DLL не запускались. Ничего не установлено и не записано в game/saves.
[Предыдущая подготовка](STAGE10_10_1_PHASE_D_PREPARATION_HISTORY.md) сохранена как история.

## Проверенная база и резервная копия

Игра: `D:\SteamLibrary\steamapps\common\Enshrouded`, build **1287369**, Steam
**26430625**, depot **7226436020230696061**, EXE 1.0.1.2.
LOCAL: `C:\Users\user\Saved Games\keen games\Enshrouded`.

Новая копия: `C:\Enshrouded-ai-companion\runtime\backups\stage10-10-1-clean-20261118`.
27/27 payload файлов проверены SHA-256: EXE, KFC, resources, local config, 23 LOCAL.
Payload **260563026 bytes**, вместе с тремя metadata-файлами **260600882 bytes**.
DAT-тел нет: hashes всех 64 оригинальных DAT записаны в baseline; 55 входят в KFC.
Копия не является полной копией игры и не предназначена для автоматического
восстановления LOCAL после будущей игровой миграции.

Manifest SHA-256: `d671fd038634433b3400682e0b0f7e513a854111b3ca96e123e76b1d1e59250a`.
Baseline fingerprint: `aeb28660e7a2d69cbbd42248fe25f900201274c5dcdabb37456926554d62e58d`.
[Backup result](../compatibility/recovery/1287369/post_steam/accepted-backup.json).

Финальная реальная проверка: **137/137 game и 23/23 LOCAL неизменны**; Steam idle,
игра/server закрыты. Прежний backup 209/209 и карантины 81/81, 31/31 сохранены.
В первом history capture обнаружено совпадение имён папок backup B/quarantine B:
ключ словаря терял одну запись. Исправлено на относительные пути для будущих
capture; старое evidence не переписывалось. Старый backup дополнительно проверен
по его pinned manifest, plan и receipt, оба карантина — по неизменным inventory.

## Готовый пакет и точный состав

Локальный пакет: `C:\Enshrouded-ai-companion\dist\stage10_10_1_phase_d_20261118`.
В game предназначены **16 файлов**, все назначения сейчас отсутствуют.
Ещё 12 лицензий/notice остаются в пакете; `install-plan.json` и
`bridge-binding.json` также не копируются в игру.

[Exact manifest: все SHA-256, размеры, source/destination, ownership и rollback](../compatibility/migration/1287369/exact-install-manifest.json).
Локальный install-plan SHA-256:
`82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463`.
Bridge binding SHA-256:
`9b06a725b8daba270db31d99120f91be6dc5878f6ea42c37d10ee504033237b4`.

| Путь относительно игры | Назначение |
|---|---|
| `dinput8.dll` | Официальный loader 0.6.18 |
| `emf/emf_core.dll` | Core API46, Bridge protocol1 |
| `emf/emf_content.dll` | Единственный integrated content owner |
| `emf/mods/lua/lua.dll` | Lua host 1.39.0 |
| `emf/mods/lua/mod.json` | Официальный manifest host |
| `emf/known_tools.txt` | Официальная классификация loaders/tools |
| `emf/emf_core.ini` | content=on, log_opens, Bridge/diagnostics |
| `emf/config/lua.ini` | Включён только требуемый host |
| `mods/aic_eml_humanoid/mod.json` | Patch 0.5.0, только capability patch |
| `mods/aic_eml_humanoid/src/mod.lua` | Сгенерированный самостоятельный entry point |
| `mods/aic_eml_humanoid/README.md` | Инструкция 0.5.0 |
| `emf/mods/aic_integrated_observer/mod.json` | Observer 0.3.0/API46 |
| `emf/mods/aic_integrated_observer/main.lua` | Read-only команды |
| `emf/mods/aic_integrated_observer/binding.lua` | Новый private run/plan/profile binding |
| `emf/mods/aic_integrated_observer/README.md` | Ограничения observer |
| `emf/config/aic_integrated_observer.ini` | Включение observer |

Официальный архив — ранее проверенный `EMF-0.6.18-manual.zip`,
SHA `12bbcae2e52386bcd7f1747701bb6d1ec8a64fab061e6e33ce994b6ee29c926b`.
При упаковке заново сверены archive SHA и каждый используемый member с pinned
release index. Ранее установлено: DLL x64/PE32+, Authenticode NotSigned; повторная
проверка подписи не заявляется. Binary/source воспроизводимость не доказана.
Архив/DLL остаются локально, в Git публикуются только metadata и наши исходники.
Manager, installer, standalone EML/dbghelp, Companion/Beastmaster/Villager Jobs,
legacy `aic_body` и старые observers в пакет не входят.

## Patch, evidence, observer и Bridge

[Patch library](../experimental/integrated_humanoid/patch.lua) превращается builder
в полноценный `src/mod.lua` с baseline/profile/deployment contract. Старый patch
0.4.0 сохранён без изменений. Новый patch проверяет точный KFC version string,
source 82 components/FNV `5253f478`, девять typed `.value` UInt32, gender/proportions,
graph, RenderEquipment, 63 resource dependencies, hierarchy 102 joints,
18 конкретных preset reference slots, отсутствие clone и npcId среди 12269 templates.

После `create_resource` проверяются composite identity GUID/type/part и lookup.
Сравниваются все отражённые значения source до/после, все компоненты clone и все
поля, кроме разрешённых overrides: clone name, Faction.faction=PlayerAlly и npcId.
Число PlayerAlly=11 проверяется через актуальную enum metadata. AI/persistence/
animation компоненты не удаляются. Это изменение ресурса будущей shadow build,
а не создание или изменение игровой сущности.

Canonical comparison работает с mapped structs/arrays/variants; непонятный тип
останавливает build. Integer comparison сохраняет 64-битную точность Lua integer.
FNV служит диагностическим отпечатком, не криптографической аутентификацией.
Привязка к исходным файлам проверяется отдельными SHA-256.

Evidence v8: **40 обязательных полей + BEGIN/END**, отсортированный набор,
проверка количества и FNV framing; `print → emf/content.log`, без `io.export`.
Дубликаты, обрыв, старый run, смешанные кадры, неверный профиль/UInt32/provenance
отклоняются. Frame checksum не является подписью. Writer status намеренно
`REQUESTED_NOT_FINALIZED`; build evidence не подтверждает writer close или render.

[Observer](../mods/aic_integrated_observer/main.lua) имеет реальный manifest,
bootstrap и generated binding. Регистрируются только status/inspect/compare.
Lua сообщает session token/session и имя персонажа, отвечает на свежий nonce.
Он не обращается к EML `game.assets` после выгрузки content DLL. Slot, LOCAL storage,
world name, build/API/host проверяет [клиент](../companion/integrated_client.py)
через подтверждённые Bridge hello/state до и после команды. Невозможные из Lua
наблюдения не заменяются значениями из запроса. Inspect/compare дополняются
проверкой локальных v8 frames в Python. Старый mutation BodyClient не расширялся.

План связан с fresh run через SHA token в plan identity. Observer содержит plan ID
и profile SHA; будущий receipt будет ссылаться на SHA всего install-plan и 16
installed hashes. Это избегает циклического hash «receipt включает свой hash внутри
установленного файла». **Настоящего install receipt пока нет.**

Подтверждённые реализации в локальном checkout EMF commit
`fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`:

- `third_party/eml/crates/mod-loader-lua/src/env/game/assets.rs`,
  `assets/resource.rs`, `assets/value/mapped.rs`, `types.rs`: resource creation,
  lookup, reflection, `.value`, `pairs`, enum metadata.
- `src/lua_host/host.cpp`: emf.command/reply/session/session_token/local_player;
  `src/core/bridge/state.cpp`, `service.cpp`, `mod_registry.h`: реальные поля и statuses.
- `src/loader/content_fingerprint.h`, `content_state.h`, `content_build.h`,
  `eml_mods.h`: fingerprint algorithm, writer state и формат mod IDs.

Общее происхождение и прежний аудит:
[EMF 0.6.18 source](https://github.com/matenm/emf-enshrouded/tree/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241),
[аудит совместимости](STAGE10_10_EMF_COMPATIBILITY.md).
Новые сетевые исследования ранее подтверждённых механизмов не выполнялись.

## Shadow, writer, rollback и следующие фазы

[Shadow validator](../companion/shadow_integrity.py) используется с
`base_dat_count=55`: EXE и 55 base DAT имеют ожидаемые hardlinks; KFC/resources и
generated DAT — private files. Девять сохранённых original DAT055–063 остаются
нетронутыми. Оригинальные hash/identity/link count/mtime проверяются отдельно.
Подробности: [Shadow integrity](STAGE10_10_1_SHADOW_INTEGRITY.md).

[Writer validator](../companion/integrated_writer.py) воспроизводит pinned
metadata fingerprint: size/FILETIME/relative names + build inputs, **не** file hashes.
Fixture отдельно показывает его ограничение: изменение содержимого при той же
длине/mtime не меняет upstream fingerprint. Поэтому SHA-проверки обязательны.
Принимается только code0, unloaded=true, truncated=false, ожидаемый patch,
отсутствие errors/warnings, новый built_at в окне текущего запуска и independently
recomputed input fingerprint. Это только state gate, не shadow readback/redirection.

Новый rollback planner проверяет current-build receipt, точный список, installed
hashes и links. Dry-run **16/16** выполнен на копии пакета в project runtime;
ничего не удалялось. При наличии runtime shadow planner останавливается с
`SHADOW_REQUIRES_FRESH_ATTRIBUTION_AND_LINK_AUDIT`: нельзя заранее приписать ещё
не созданные файлы установщику. После Phase F нужен отдельный audited manifest
shadow с проверкой private/hardlink, без рекурсивного удаления неизвестного.
Оригиналы KFC/DAT и LOCAL не восстанавливаются автоматически. Старый rollback1273043
не используется. [Фактический verification result](../compatibility/migration/1287369/offline-verification.json).

Phase E после отдельного разрешения: повторить stopped/Steam/baseline/backup/source
checks; установить только 16 entries с сохранением immutable transaction history;
получить новый current-build receipt; проверить 16/16 и rollback dry-run; остановиться.
При любой ошибке — сохранить фактическое частичное состояние, не продолжать и не
править receipt вручную. Не запускать game/server, не выполнять writer/spawn.
Следующий игровой load-only тест — отдельная Phase F по
[плану](STAGE10_10_1_LOAD_ONLY_PLAN.md).

## Ответы на 21 пункт ТЗ

| № | Подтверждение / ограничение |
|---|---|
| 1 | После Steam восстановлена локально проверенная база; PARTIAL принят пользователем, не переименован в CONFIRMED |
| 2 | Исторически Phase B81 + Phase C31 файлов в отдельных карантинах; на этой фазе новых перемещений нет |
| 3 | 20 KEEP сохранены; полный текущий inventory137 включает также 59 старых backup/logs и другие исторические записи |
| 4 | Steam заменил 9 KFC chunks и убрал 4096-byte хвост resources; детали в post-Steam audit |
| 5 | Internal1287369 / Steam26430625 / EXE1.0.1.2 |
| 6 | Новая clean copy260600882 bytes; прежняя limited copy420406619 bytes; вместе681007501 bytes, без карантинов |
| 7 | 23/23 LOCAL совпадают с принятой базой и включены в новую копию |
| 8 | Старый clone отсутствует по принятому post-Steam scan; файлы базы сейчас те же SHA |
| 9 | hunter_assistant сохранён; повторное исследование неизменённых ресурсов не понадобилось |
| 10 | 82 компонента, fingerprint5253f478 |
| 11 | 18 refs/102 joints/graph подтверждены ранее clean readback; сейчас offline fixture и strict candidate guards; render UNKNOWN |
| 12 | Patch0.5.0 installable candidate готов, исторический0.4 не изменён |
| 13 | 16-file integrated package готов; официальные бинарники только локально |
| 14 | Observer0.3.0 готов, Lua fixture/syntax PASS; actual host loading ещё не проверялся |
| 15 | Read-only Bridge client готов, fake transport tests PASS; live connection не выполнялось |
| 16 | Полный137-file SHA inventory, receipt/file hashes и контроль ссылок; LOCAL отдельно |
| 17 | Base55/private shadow validator + будущий Inspector readback + свежие writer/state/redirect evidence |
| 18 | Exact manifest готов, plan SHA закреплён выше; real install receipt появится после разрешённой установки |
| 19 | Полный Python suite, compileall, Lua syntax, 82-component decoded-source fixture, backup/preflight и rollback fixture; см. TEST_RESULTS |
| 20 | Офлайн-блокеров нет при принятом PARTIAL; runtime binary compatibility, сериализация, redirect, render и spawn safety пока неизвестны |
| 21 | Можно запросить Phase E для этих16 файлов; разрешение ещё не получено, Phase F/spawn сюда не входят |

Результаты тестов: [TEST_RESULTS](TEST_RESULTS.md). Успешные fixtures не выданы за
игровое испытание. Даже будущий LOAD_ONLY_SUCCESS оставляет `spawn_ready=false`.
