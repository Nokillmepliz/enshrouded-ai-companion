# Журнал прогресса Enshrouded AI Companion

## 2026-11-01 — этап 10.5, части B/C завершены

- Из официальных источников локально в `.tools` установлены Rust/Cargo 1.88.0 (`x86_64-pc-windows-gnu`) и MSYS2 MINGW64 GCC 16.2.0/binutils 2.47 без admin, системной установки и постоянного PATH. Rust bootstrap SHA-256 совпал с опубликованным; MSYS2 archive получил `GOODSIG/VALIDSIG` от subkey `E0AA…4964`. User PATH/Rust env не изменены.
- Создан `Cargo.lock` v4 (42 packages), проверены registry checksums, pinned KFC commit и активные build scripts. Неизвестных сетевых/autostart/write-outside-OUT_DIR действий не найдено.
- KFC Inspector собран в игнорируемый `.tools/kfc-inspector/bin`; итоговый SHA-256 `fb106699dd0edad8afa5d39b4264c3ed29652099882a573cfd6f207db49be0c8`. Добавлены безопасные exact-type index и single-GUID type lookup; KFC writer/create/patch API отсутствуют.
- Rust tests: 2 PASS. Python suite: 218 PASS, 1 SKIP; отдельный Windows junction test PASS. Malformed/missing GUID и unknown type отклонены реальным бинарником без output. Skip относится только к privileged symlink fixture.
- Read-only декодированы `hunter_assistant` и `blacksmith_assistant` (по 81 component), `CharacterPresetCollection` (54 presets), `ItemRegistryResource` (4207 refs/names), 24 связанных `ItemInfo`, 35/35 `RenderModel` и общий `ModelHierarchyResource` на 102 joints.
- Подтверждена source visual chain `Template → preset → ItemInfo → RenderModel → hierarchy`. `RenderEquipment.lastModels` в template пустой runtime output. Clone reference equality и runtime render остаются UNKNOWN; canonical fingerprint не повышен, `spawn_ready=false`.
- SHA-256 до/после полностью совпал для 210 файлов: 62 game files (включая 55 DAT), 23 LOCAL saves и 125 Steam saves. Added/removed/changed отсутствуют.
- Enshrouded не запускался, EML не устанавливался, KFC/DAT/DLL/saves/entities не изменялись. Статус этапа: **PARTIAL_SUCCESS**.
- Исходники inspector, `Cargo.lock`, integrity tooling, тесты и отчёты опубликованы в `origin/master`; основной implementation commit: `2180fdf`.
- Следующий шаг: отдельно согласованный load-only export точных `CharacterSetup` и preset/item/model references у EML clone без spawn.

## 2026-11-01 — этап 10.5, контрольная точка A

- Прочитаны ТЗ и история 10.2–10.4; `master` исходно совпадал с `origin/master` на `87fc2fb`, локальных изменений не было.
- Аудит среды подтвердил отсутствие `rustc`, `cargo`, `cl.exe`, `link.exe`, `clang-cl`, GCC/CMake/Ninja и зарегистрированных Visual Studio Build Tools. Rust и другое ПО не устанавливались.
- Pinned kfc-parser требует Rust 1.88.0/edition 2024. Upstream lock подтвердил цепочку `zstd 0.13.3 -> zstd-sys 2.0.15 -> cc 1.2.48`; поэтому одного Rust недостаточно, необходим native C compiler/linker.
- Усилен source-only inspector: canonical output parent, запрет game path/overwrite/collision, `create_new`, read-only input opens и удаление только нового частичного report при ошибке finalize. KFC writer/patch/create APIs отсутствуют.
- Добавлен offline audit module и синтетические тесты toolchain/version/manifest/dependencies/path/symlink/KFC4/hash/deterministic JSON. Rust unit tests подготовлены, но не запускались.
- Полный offline suite: **216 PASS, 1 SKIP**; skip — недоступное создание Windows directory symlink без привилегии. `compileall` и `git diff --check` прошли; реальный junction/symlink gate перенесён в обязательные проверки перед KFC read.
- Выполнен только ограниченный read-only header check оригинального KFC (`KFC4`); resource lookup, hunter/blacksmith/registries extraction и pre/post game hashes не выполнялись.
- Visual fingerprint не повышен: `STRUCTURAL_MATCH=true`, остальные уровни `UNKNOWN`, `spawn_ready=false`. EML patch, observer и evaluator не менялись.
- Ограничение: собственный `Cargo.lock` отсутствует; Rust/native toolchain, сборка, binary SHA-256 и KFC extraction ждут отдельного разрешения и успешного safety audit.
- Следующий шаг: согласовать способ получить локальные Rust 1.88.0 и native C compiler/linker без глобального PATH/админ-установки; затем создать и проверить lock до build.

## 2026-10-31 — этап 10.4, RenderEquipment и visual resources

- Pinned EMF reflection разобран новым read-only `tools/reflection_schema.py`. Подтверждены все поля шести целевых компонентов и вложенных `Equipment`, `ItemVisual`, `ItemRenderColors`, `HashKey32`.
- `RenderEquipment` — dynamic/client-only data component: 24 runtime handles, 24 GUID `lastModels`, цвета, masks и render pose. `CharacterSetup` хранит gender/preset/hair/beard/colors как U8/HashKey32. `NewCharacterSetup` и `EquipmentCheck` — server-only маркеры; `InventorySetup` хранит entity links, не model GUID.
- ECS program map подтвердил цепочку: `apply_charactersetup` использует preset/item registries и inventory, `equipment_visuals` пишет `Equipment`, `render_equipment_models_ag2` пишет `RenderEquipment` и `RenderScene`. Конкретные model/mesh/skeleton GUID остаются неизвестны.
- Создан standalone fail-closed visual fingerprint contract: текущий evidence даёт только `STRUCTURAL_MATCH`; resource match/dependency resolution/runtime render остаются `UNKNOWN`, `spawn_ready=false`.
- Подготовлен source-only Rust inspector `tools/kfc_readonly_inspect` на pinned kfc-parser. Read-only preflight оригинального KFC подтвердил `KFC4` и `writes_performed=false`, но `cargo`/`rustc` отсутствуют. Бинарник не собран и не запускался; системные инструменты не устанавливались.
- EML patch, Stage 10 evaluator и observer не менялись: доказательств для нового обязательного visual-контракта недостаточно.
- Полный offline suite: **205 PASS**; `compileall`, Lua validation существующих модов и `git diff --check` прошли. Rust source не компилировался и не включён в число runtime-проверок.
- Созданы `STAGE10_4_VISUAL_RESOURCE_RESEARCH.md` и `STAGE10_4_VISUAL_FINGERPRINT_DESIGN.md`. История этапов 10.2/10.3 сохранена.
- Enshrouded не запускался; EML, игровые DLL/KFC/DAT/сохранения/entities/inventory/equipment не изменялись.
- Статус: **BLOCKED**. Следующий шаг требует отдельного разрешения на локальный Rust 1.88 toolchain, сборку/audit inspector и read-only KFC extraction.

## 2026-10-31 — этап 10.3, диагностика человеческой модели

- Причина `model_guid=nil` установлена: в реальном component fingerprint source и clone этапа 10.2 нет `keen::ecs::ModelResource`. `nil` возник при поиске компонента. Pinned EML source подтверждает: отсутствующее mapped field возвращает nil, а присутствующий GUID возвращается Lua-строкой.
- Оригинальные KFC build 1273043 прочитаны только для SHA-256 и binary string search. Структурный dump получить не удалось: проверенного read-only parser-бинарника и Rust toolchain нет; официальный EMM не запускался из-за его patch-capable execution path.
- `hunter_assistant` и `blacksmith_assistant` офлайн структурно сравнить нельзя. Точная цепочка от `RenderEquipment`/setup до mesh/skeleton остаётся `UNKNOWN`.
- EML patch обновлён до 0.2.0 и typed evidence v2. `MISSING`, `UNSUPPORTED` и `CONFIRMED` различаются; GUID-object/неверный тип не строкифицируются в ложное подтверждение.
- Evaluator требует два реальных UUID по подтверждённому контракту и их равенство. Observer обновлён под v2 и остаётся read-only/compact. `spawn_ready=false` сохранён.
- Полный offline suite: **193 PASS**; `compileall`, Lua compile и `git diff --check` прошли. Три observer-ответа декодируются и укладываются в лимит 1023 байта в тестовом worst-case evidence.
- Созданы `STAGE10_3_MODEL_RESOURCE_RESEARCH.md` и `STAGE10_3_MODEL_FINGERPRINT_FIX.md`; результат 10.2 не переписан.
- Enshrouded не запускался, EML не устанавливался, игровые файлы/KFC/DAT/сохранения не изменялись, NPC не создавались.
- Статус этапа: **BLOCKED**. Настоящий model fingerprint и blacksmith comparison не получены; повторный load-only требует отдельного разрешения и сам по себе не разрешает spawn.

Обновляется после каждой завершённой задачи. Записи сохраняют историю: выполненные действия, проверки, блокеры и запланированные следующие шаги. Планы не означают разрешения на установку или игровые изменения.

## 2026-10-30 — Подготовка этапа 3: первое игровое испытание

Статус: подготовка завершена. Версия игры поддерживается EMF, но к игровому запуску комплект пока не готов: отсутствуют DLL EMF.

### Совместимость

Установленный EXE по SHA-256 точно соответствует клиентской сборке **1273043** из [таблицы совместимости EMF](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/common/signatures.cpp#L11-L15). Steam BuildID — **26082781**; это другой идентификатор.

SHA-256 EXE:

```text
d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882
```

Совпадение подтверждает поддержку версии в исследованном EMF 0.3.2, но не подтверждает загрузку адаптера и поведение сущности в реальной игре. После обновления Steam проверку нужно повторить.

### Точные пути

| Объект | Путь |
|---|---|
| Проект | `C:\Enshrouded-ai-companion` |
| Игра | `D:\SteamLibrary\steamapps\common\Enshrouded` |
| Steam-сохранения | `C:\Program Files (x86)\Steam\userdata\<SteamUserID>\1203620` |
| Локальные настройки/сохранения | `C:\Users\user\Saved Games\keen games\Enshrouded` |
| Архив адаптера | `C:\Enshrouded-ai-companion\dist\aic_body-0.1.0.zip` |
| Подготовленный Python | `C:\Enshrouded-ai-companion\.tools\python\python.exe` |
| Будущие резервные копии | `C:\Enshrouded-ai-companion\runtime\backups` |
| Логи клиента | `C:\Enshrouded-ai-companion\runtime\logs` |

На момент проверки найдено 104 файла Steam-сохранений, около 28 МиБ. В локальном каталоге есть только `local_settings.json`; отдельного LOCAL тестового мира пока не обнаружено.

### Адаптер и необходимые файлы

**Собственной DLL у адаптера нет:** это Lua-мод EMF. Архив проверен и содержит `mod.json`, `main.lua`, `body.lua`, `json.lua`. Для загрузки нужны файлы официального EMF 0.3.2:

```text
Enshrouded\
  dinput8.dll
  emf\
    emf_core.dll
    known_tools.txt
    vk\VkLayer_EMF_console.json
    mods\lua\lua.dll
    mods\lua\mod.json
    mods\aic_body\mod.json
    mods\aic_body\main.lua
    mods\aic_body\body.lua
    mods\aic_body\json.lua
```

Это критические компоненты, а не инструкция выборочно копировать DLL из пакета. Подробный состав и будущие ini-настройки приведены в [STAGE3_PREFLIGHT.md](STAGE3_PREFLIGHT.md).

Бинарный пакет EMF ещё не получен и не проверен. На [странице Nexus](https://www.nexusmods.com/enshrouded/mods/246) при проверке была отметка сканирования «Some suspicious files» — перед установкой нужно разобраться с конкретным архивом. Нативная загрузка в игру пока не подтверждена. Отдельный C++/DLL-порт адаптера не создавался.

### Выполнено и проверено

- Добавлены подробные JSONL-логи Python-клиента: команды, ответы, время, request ID, epoch и ошибки. Каталог — `runtime/logs`.
- В Lua-мод добавлены журналы запросов и переходов состояния тела.
- Подготовлены [scripts/backup.py](../scripts/backup.py) и [config/first-test-backup.json](../config/first-test-backup.json). По умолчанию скрипт только рассчитывает копию; при явном запуске копирования проверяет SHA-256 каждого файла и не изменяет источники.
- Расчёт резервной копии: **216 файлов, 51 887 751 684 байта (48,32 ГиБ)**. Свободно около 577 ГиБ на C:, места достаточно. **Сама резервная копия ещё не создана.**
- **56 тестов прошли**; проверка Python через `compileall` и пересборка ZIP успешны. Это результаты подготовки этапа 3, не реальное игровое испытание.
- Архив содержит ровно четыре файла адаптера, DLL отсутствуют, мод выключен по умолчанию.

SHA-256 архива после добавления журналирования:

```text
e9fb551e69bed8ba2f26884436b3b9c6c7b4bf4bea48df3a67d8641778e391ff
```

### Дальнейшие действия — план, ещё не выполнены

1. Получить и проверить официальный пакет EMF.
2. После завершения синхронизации выйти из Steam и создать проверенную резервную копию.
3. После отдельного подтверждения установить EMF и адаптер, включить bridge, отключить посторонние моды.
4. Пользователь самостоятельно запускает игру через Steam, создаёт отдельные **LOCAL** персонажа и мир. До спавна сохранить их исходное состояние.
5. Проверить подключение из PowerShell:

   ```powershell
   Set-Location 'C:\Enshrouded-ai-companion'
   $Python = '.\.tools\python\python.exe'
   $Game = 'D:\SteamLibrary\steamapps\common\Enshrouded'
   & $Python -m companion diagnose --game $Game
   & $Python -m companion status --game $Game
   ```

6. Выполнять **spawn → follow → stay → dismiss** по одной команде, проверяя `succeeded` и поведение в мире. После dismiss должны исчезнуть тело и маркер.
7. При неизвестном исходе читать статус прежнего request ID; повторный spawn не отправлять.

Все команды с параметрами, настройки, критерии успеха и разбор ошибок — в [пошаговой инструкции этапа 3](STAGE3_PREFLIGHT.md).

**Граница выполненной работы:** игру не запускали, bridge к игре не подключали, моды не устанавливали, файлы игры и сохранения не изменяли. Для установки и игровых испытаний требуется отдельное подтверждение пользователя.

## 2026-10-30 — Ведение журнала прогресса

- По просьбе пользователя создан `docs/PROGRESS.md`; в него перенесены итоги предыдущего ответа о подготовке этапа 3, включая пути, совместимость, список файлов, проверки, блокеры и порядок запуска.
- В корневом [AGENTS.md](../AGENTS.md) закреплено обновление журнала после каждой завершённой задачи и чтение перед продолжением работы.
- Проверка: содержание сверено с существующим отчётом этапа 3. Код не менялся; тесты для этой задачи повторно не запускались.
- Следующий шаг остаётся прежним: получить и проверить пакет EMF, затем перейти к согласованной установке и игровому испытанию. Запрос на ведение журнала не даёт разрешения на эти действия.

## 2026-10-30 — Публикация проекта в GitHub

- По прямому запросу пользователя выполнен push в ветку `master` репозитория [Nokillmepliz/enshrouded-ai-companion](https://github.com/Nokillmepliz/enshrouded-ai-companion).
- Основной коммит `3c2e2d7` (`Add EMF body adapter, Python client and first-run preparation`) добавил 34 файла: код адаптера и Python-клиента, тесты, документацию, правила работы, скрипты и конфигурацию резервирования, vendored bridge с лицензией.
- GitHub подтвердил отправку `2ef0d9e..3c2e2d7` в `master` и сообщил канонический адрес репозитория со строчными буквами в имени.
- Перед коммитом выполнены `git fetch origin`, проверка совпадения локальной и удалённой веток, состава файлов и `git diff --cached --check`. Совпадений с проверенными шаблонами токенов/приватных ключей не найдено; это не полный аудит секретов. Код не менялся, ранее пройденные 56 тестов для этой задачи повторно не запускались.
- По `.gitignore` не публиковались `.research`, `.tools`, `.venv`, `runtime` (логи, личность и резервные копии), `dist` и Python-кеши. Архив адаптера воспроизводится из опубликованных исходников командой `python scripts/package.py`. Существующий `test.txt` сохранён.
- Эта запись фиксирует успешную публикацию основного коммита и включается отдельным коммитом документации.
- Игру не запускали, моды не устанавливали, игру и сохранения не меняли. Следующий игровой шаг по-прежнему требует отдельного подтверждения.

## 2026-10-30 — Техническое ревью и исправления перед первым игровым испытанием

Архитектура Lua Body Adapter + Python Bridge сохранена. Изучены main.lua/body.lua, Python-клиент/CLI и pinned EMF commit `08d600155fcadc8e45cc9c6f3932a67c717345be`. Исходники читались из локальной исследовательской копии; попытки получить дополнительные страницы через web завершились Cache miss, поэтому выводы опираются на доступный pinned source, а не на неподтверждённый новый API.

### Найдено и исправлено

| Проблема | Исправление |
|---|---|
| Rollback по голому ID, когда fingerprint отсутствует | ID сохраняется до reflection как неподтверждённый; destroy запрещён, поздний fingerprint не присваивает владение |
| Ошибка Faction и общий recovery блокировали даже безопасную очистку | Сохранённый подтверждённый handle можно очистить явным dismiss с обычным preflight; другие команды в recovery запрещены |
| Spawn=0 считался доказанным отказом | Native wrapper возвращает 0 и после SEH-ошибки. uncertain_spawn выставляется до вызова; lock и запрет повторного spawn сохраняются |
| Destroy повторялся каждый тик; false мог означать частичный нативный эффект | Для handle выполняется максимум одна попытка destroy. True/false/исключение различаются в диагностике; дальнейший dismiss только наблюдает уже затронутый объект и обрабатывает ещё не затронутые подтверждённые handle |
| Потеря позиции считалась исчезновением | Проверяется подтверждённый `world:entities()` с присутствием локального игрока; нужны три последовательных callback без ID |
| Временное несовпадение/исчезновение ID могло забываться | Наблюдённая потеря идентичности запоминается; прежний ID/fingerprint не восстанавливает право на изменение |
| Ошибка чтения lock выглядела как отсутствие; смена session обходила старый lock | Различаются отсутствие и ошибки I/O; проверяются write/flush/close/readback. Любой старый/нечитаемый lock и потерянное владение сохраняют блокировку после reload/смены мира/процесса |
| Lock снимался без проверки владельца | Проверяется полное содержимое с epoch контроллера до os.remove и отсутствие после. Чужой/исчезнувший/недоступный файл не даёт ложного успеха |
| Не было явного продолжения после таймаута dismiss | cleanup_timeout сохраняет handle/lock; новый dismiss ID продолжает очистку/наблюдение. Failed-ID остаётся историческим failed, эффекты сами не повторяются |
| Успех команды можно было спутать с поведением NPC | Добавлены phase/event_submission/state_confirmed/behavior_verified; behavior_verified всегда false до отдельного ручного протокола игры. Краткая близость не доказывает follow |

### Проверки и артефакты

- **87 тестов PASS**: 56 прежних (с исправленными ожиданиями) и 31 новый тест ошибок/восстановления.
- Проверены реальные Lua io.open/write/flush/close/read/os.remove во временном каталоге при поддельном EMF. Эти функции доступны и не объявляются запрещёнными.
- `compileall` и `git diff --check`: PASS. CLI help проверен без подключения к игре.
- Пересобран `dist/aic_body-0.1.0.zip`; SHA-256: `c40603f062b6a55b2a3c79fb31cfee4172a8f26f93ed676d23cc33450c8c3e91`.
- Новый клиент требует `safety_revision=2`, поэтому не отправляет изменения через старую ревизию Lua-мода. Wire protocol=1 сохранён.
- Обновлены [PROTOCOL.md](PROTOCOL.md), [TEST_PLAN.md](TEST_PLAN.md), [TEST_RESULTS.md](TEST_RESULTS.md), инструкции первого запуска и README. Порядок восстановления различает безопасный dismiss в текущей сессии и отдельно согласуемое восстановление тестового мира при потере владения.

### Оставшиеся риски и следующий шаг

- Подтверждённого generation ID экземпляра не найдено: EntityId — uint32; generation в Lua-host относится к callback; StoredSceneId.uniqueId не подтверждён как уникальный ID нашего NPC. Полностью одинаковую замену между наблюдениями нельзя исключить.
- Только игра подтвердит компоненты Vukah/маркера, фракцию, реальные события, длительное движение/бой, очистку save и производительность перечисления entities. Ошибка Faction/fingerprint может оставить враждебное тело.
- При неизвестном ID, зависшем удалении или hot reload с потерей handle безопасной автоматической очистки нет: требуется проверенная резервная копия и отдельно согласованный offline restore. Один перезапуск не снимает блокировку.
- Lua flush не гарантирует сохранность при отключении питания; проверка lock/remove не атомарна между процессами. Поддерживается один процесс игры без внешнего редактирования lock; реальные ACL/антивирус в каталоге игры не испытывались.
- **Игровые проверки NOT RUN.** EMF не устанавливался, игра не запускалась, игровые файлы/сохранения не менялись. Следующий игровой шаг — проверка дистрибутива EMF, backup и отдельное подтверждение пользователя.
- По запросу пользователя изменения закоммичены и отправлены в `origin/master`: **`026cd8a` — Harden body identity, partial cleanup and runtime lock recovery**. GitHub подтвердил push `7ae9e16..026cd8a`. Эта запись о результате отправки сохраняется отдельным коммитом документации.

## 2026-10-30 — Аудит официального дистрибутива EMF 0.3.2

- Получен официальный GitHub Release asset `EMF-0.3.2-manual.zip` в отдельный каталог проекта `artifacts/emf-0.3.2-audit`; в игру он не копировался. Каталог `artifacts/` добавлен в `.gitignore`, поэтому бинарники EMF не будут опубликованы в репозитории.
- Размер архива — **5 142 221 байт**, SHA-256 — **`737d3614b9462f00e942828869054b842e7af6d7b9abe56402e2a0bde35d00d9`**. Хеш точно совпал с digest asset в публичном GitHub API.
- Тег `v0.3.2` указывает на исследованный commit `08d600155fcadc8e45cc9c6f3932a67c717345be`; GitHub Actions run тега завершился успешно. Критические скрипты и Python bridge из архива побайтно совпали с pinned source. Встроенная версия core и структура package соответствуют source workflow/package script.
- Полная source-to-binary identity не доказана: DLL не пересобирались воспроизводимо, GitHub attestation не найден, все 16 PE-файлов unsigned. Совпадение номера версии не использовалось как самостоятельное доказательство.
- Проверено 239 записей архива: unsafe paths, дубликатов имён и вложенных архивов нет. Manual-пакет не содержит `EMF.exe`; найдено 15 DLL и одна диагностическая EXE. Все PE — x64/PE32+, статические зависимости только системные Windows DLL.
- Установочные скрипты не содержат сетевого скачивания, служб, Scheduled Tasks, Run/RunOnce или изменения Defender/firewall и не запускаются автоматически. `install.cmd` использует `ExecutionPolicy Bypass`, поэтому будущий план вызывает проверенный `install.ps1` напрямую.
- Microsoft Defender platform `4.18.26100.4`, signatures `1.463.34.0` не нашёл угроз ни в ZIP, ни в распакованном каталоге; оба custom scan завершились с кодом 0. Это один движок и не снимает риск Nexus quarantine.
- Nexus Mods по-прежнему показывает `Some suspicious files`/quarantine для обоих основных архивов. Конкретный гостевой отчёт с названиями детектов недоступен; объяснение автора связывает предупреждение с `dinput8.dll` hooking и unsigned `EMF.exe`, но это не независимое доказательство безопасности.
- Совместимость с установленной игрой подтверждена повторно: SHA-256 `enshrouded.exe` — `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882`, точное совпадение с client build `1273043` в таблице EMF. Steam BuildID `26082781` остаётся отдельным идентификатором.
- Lua host в архиве — 1.9.0 / EMF API 20; требования `aic_body` — Lua >=1.8 / API 20. Bridge-файлы совпадают с source. Это подтверждает статическую совместимость, но не фактическую загрузку в игре.
- Создан подробный [EMF_DISTRIBUTION_AUDIT.md](EMF_DISTRIBUTION_AUDIT.md) с источниками, всеми PE-хешами, составом, предупреждением Nexus, планом установки/отката и рисками. Вердикт: **`READY_FOR_BACKUP_AND_INSTALL_REVIEW`**.
- Полный локальный запуск `.tools/python/python.exe -m unittest discover -s tests -q`: **87 тестов PASS**. `compileall` для `companion`, `scripts`, `tests` и `git diff --check`: PASS.
- Граница работы соблюдена: EMF не устанавливался, игра и скачанные PE не запускались, каталог игры и сохранения не менялись, резервная копия не создавалась. Следующий шаг требует отдельного разрешения пользователя.
- Отчёт, `.gitignore` и результаты проверки опубликованы в `origin/master`: основной коммит аудита **`dfd3f1e` — Audit official EMF 0.3.2 distribution**. Бинарники EMF в push не входили; эта строка о результате отправки сохраняется следующим журнальным коммитом.

## 2026-10-30 — Малая копия сохранений и установка EMF/aic_body

Пользователь явно разрешил сделать небольшую копию сохранений и установить ранее проверенные EMF 0.3.2 manual и `aic_body`, без запуска игры и spawn. Полная копия каталога игры на 48 ГиБ по указанию пользователя не создавалась.

### Проверки до установки

- Steam был запущен, Enshrouded и dedicated server не работали. Steam завершён штатной командой `steam.exe -shutdown`; перед копированием и установкой проверено отсутствие процессов `steam`, `enshrouded`, `enshrouded_server`.
- В `D:\SteamLibrary\steamapps\common\Enshrouded` отсутствовали `dinput8.dll`, `dinput8-chain.ini`, каталог `emf`, а также типичные proxy `dbghelp.dll`, `winmm.dll`, `version.dll`, `dxgi.dll`. Конфликтующий mod loader не найден.
- Повторно сверены SHA-256:
  - `EMF-0.3.2-manual.zip`: `737d3614b9462f00e942828869054b842e7af6d7b9abe56402e2a0bde35d00d9`;
  - `dist/aic_body-0.1.0.zip`: `c40603f062b6a55b2a3c79fb31cfee4172a8f26f93ed676d23cc33450c8c3e91`;
  - `enshrouded.exe`: `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882` — поддерживаемая сборка 1273043.
- Microsoft Defender повторно проверил ZIP и распакованный EMF: угроз не найдено, оба exit code 0. Защита и real-time protection оставались включены; предупреждения не обходились.

### Резервная копия сохранений

- Добавлена конфигурация [first-test-saves-backup.json](../config/first-test-saves-backup.json): только Steam userdata приложения `1203620` и `%USERPROFILE%\Saved Games\keen games\Enshrouded`; каталог игры и appmanifest не копируются.
- Проверенная копия: `C:\Enshrouded-ai-companion\runtime\backups\20261030T182034Z-e435bc1c`.
- Манифест: `C:\Enshrouded-ai-companion\runtime\backups\20261030T182034Z-e435bc1c\manifest.json`, `mode=completed`, `verified=true`.
- Скопировано **105 файлов, 29 352 671 байт**. Скрипт сравнил SHA-256 записанного потока, повторно прочитанного источника и копии. Дополнительная независимая проверка всех 105 источников/копий дала **0 ошибок**; после установки проверка повторена, исходники сохранений не изменились.
- Штатный installer EMF также сообщил о собственной starter-копии 9 файлов/2,3 МБ в `C:\Users\user\AppData\Local\EMF\save-backups\2026-10-30_21-20-57_starter`. Это дополнительная копия, основной проверенный набор находится в проекте.

### Установка и конфигурация

- Официальный `install.ps1` из проверенного manual-пакета выполнен с явными `-Game 'D:\SteamLibrary\steamapps\common\Enshrouded' -IfBackupFails Stop`. Результат installer: **69 файлов скопировано**, 0 существующих settings сохранено, 0 старых файлов удалено.
- Все 69 runtime-файлов после установки побайтно сверены по SHA-256 с распакованным проверенным пакетом: **0 отсутствующих/несовпадающих**. `emf\installed.txt` содержит 69 записей.
- Ключевые установленные хеши:
  - `dinput8.dll`: `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee`;
  - `emf\emf_core.dll`: `3b2b3ddd4c3a9696dd69389ba49d33af5b5f9d1377ed44bde3cd2a73778417f3`;
  - `emf\mods\lua\lua.dll`: `e12342a5e4b61355cf8665d4179572d3da684cc61fb4902c38de9fb4bcc28fef`.
- `aic_body` распакован в `D:\SteamLibrary\steamapps\common\Enshrouded\emf\mods\aic_body`. Двойной вложенности нет; `mod.json`, `main.lua`, `body.lua`, `json.lua` точно совпали с исходниками проекта.
- Для всех 22 обнаруженных manifests созданы явные config switches. Включены только `[lua] enabled=1` и `[aic_body] enabled=1`; остальные **20 модов**, включая штатные `companion`, `clock`, `quick_stack`, `beastmaster` и `herald`, имеют `enabled=0`.
- `D:\SteamLibrary\steamapps\common\Enshrouded\emf\emf_core.ini` содержит только подтверждённую настройку bridge:

  ```ini
  [debug]
  bridge=1
  bridge_verbose=1
  ```

- После установки Defender отдельно проверил установленный `dinput8.dll` и весь каталог `emf`: угроз не найдено, оба exit code 0. Defender и real-time protection включены.
- После изменений полный запуск unit/integration suite: **87 тестов PASS**; `compileall`, dry-run новой backup-конфигурации и `git diff --check`: PASS.

### Граница и следующий шаг

- Игра не запускалась. Нативная загрузка EMF/Lua, создание named pipe и диагностика мира ещё не проверялись. `bridge.txt` вручную не создавался.
- Профиль личности пока не создавался. NPC не спавнился; команды `spawn`, `follow`, `stay`, `dismiss` не выполнялись.
- Пользователь должен запустить Steam и Enshrouded вручную, создать/выбрать отдельные **LOCAL** персонажа `Body Test` и LOCAL мир. До spawn выполнить только проверку `mods`, `lua.status`, затем Python `diagnose` и `status` по инструкции ниже/в [STAGE3_PREFLIGHT.md](STAGE3_PREFLIGHT.md).
- После создания нового LOCAL персонажа/мира желательно выйти из игры и Steam и сделать вторую малую копию этим же config: она зафиксирует исходное состояние именно тестового мира до spawn.

## 2026-10-30 — Первый запуск: EMF работает, overlay-консоль недоступна

Пользователь вручную запустил Steam/Enshrouded и загрузил мир. Spawn и другие команды тела не выполнялись.

- `emf_core.log` подтвердил штатную загрузку `emf_core 0.3.2`, точный build 1273043 и **50/50 usable signatures**.
- EMF loader, Lua 1.9.0 и `aic_body` 0.1.0 загрузились. В логе: `Body adapter loaded; no automatic spawn`, `running (main.lua)`, `lua ready: 1 Lua mod(s)`. Все остальные bundled-моды показаны как disabled.
- Клавиша scan code `0x29` обрабатывается, но overlay не показывается. Точная причина из лога: `the game's Vulkan device did not come through EMF's layer`. Файл `emf\vk\VkLayer_EMF_console.json` существует. Это проблема графического overlay, а не загрузки core/мода.
- Bridge запущен: `\\.\pipe\emf-bridge-94024`, protocol 1. Из обычной sandbox-сессии соединение получило Windows error 5; разрешённый read-only запуск вне sandbox успешно выполнил только `diagnose` и `status`.
- Диагностика подтверждает: `emf=0.3.2`, `api=20`, `game_build=1273043`, `process=client`, `world.status=running`, `world.kind=server`, Lua loaded, `aic_body` script.
- Состояние тела безопасное: `mode=absent`, `recovery_required=false`, `uncertain_spawn=false`, `orphaned=false`, `last_error` пуст, `safety_revision=2`. Никакая сущность не создана.
- Обнаружен блокер тестового протокола: персонаж `Body Test` имеет `character.storage=steam`, slot 4; мир `solowithai` имеет slot **260 (`0x0104`)**. Это Steam-backed набор, а план требует отдельные LOCAL character/world slots. Spawn в текущем мире запрещён до решения этого расхождения и новой резервной копии.
- Логи успешных read-only проверок: `runtime/logs/20261030T193351Z-1f914f22fb7c45fc8ec17d1842525894.jsonl` и `runtime/logs/20261030T193351Z-e3ae41dc454243578c02c9c194ecb718.jsonl`.

Следующий шаг: выйти из мира без spawn, дождаться сохранения/Steam Cloud и закрыть игру/Steam. Затем установить подтверждённый способ создать действительно local-storage тестовый набор либо отдельно пересмотреть ограничение; до этого тест сущности не продолжать. Overlay-консоль для диагностики не обязательна, поскольку bridge исправен.

### Повторная проверка после выбора локальной игры

- Пользователь создал и загрузил локальный мир. Read-only `diagnose/status` подтвердили: мир **локальный**, `world.slot=1`, имя `Мой мир 1`, `status=running`, `kind=server`.
- Персонаж остался Steam-backed: `character.storage=steam`, slot 4, имя `Body Test`. На диске появился локальный `default\world0.ksd`, но локального `character0.ksd` нет. Поэтому preflight клиента по-прежнему обязан отклонить spawn.
- Состояние адаптера после смены мира: новая session/epoch, `mode=absent`, `recovery_required=false`, `uncertain_spawn=false`, ошибок нет. Spawn не выполнялся.
- Подтверждённый upstream-порядок выбора персонажа: в главном меню рядом с персонажем нажать **Change**, открыть вкладку **LOCAL**, выбрать или создать локального персонажа; метка должна быть `[LOCAL] <name>`. Для теста нужен LOCAL slot 1–16. Выбор локального мира сам по себе не переводит Steam-персонажа в local storage.
- Логи проверки: `runtime/logs/20261030T193934Z-74370192a0044d22a9bdc17260e92c85.jsonl` и `runtime/logs/20261030T193934Z-4de91aaae3694bd087e680fac591c132.jsonl`.

Следующий шаг: выйти в главное меню, через Change → LOCAL создать/выбрать отдельного локального `Body Test`, затем снова загрузить локальный мир и повторить read-only диагностику. До подтверждения `character.storage=local` spawn запрещён.

### LOCAL-набор подтверждён

- После создания локального персонажа read-only `diagnose/status` подтвердили полный тестовый набор: мир `AI Body Test`, `world.slot=1`, `status=running`, `kind=server`; персонаж `Body Test`, `character.storage=local`, `character.slot=1`.
- EMF 0.3.2/API 20/build 1273043, Lua 1.9.0 и `aic_body` 0.1.0 подтверждены через bridge. Остальные моды остаются disabled.
- Адаптер в безопасном исходном состоянии: `mode=absent`, `recovery_required=false`, `uncertain_spawn=false`, `orphaned=false`, `last_error` пуст, `safety_revision=2`. Spawn и другие команды тела не выполнялись.
- Логи: `runtime/logs/20261030T194248Z-21c1739f9b324a8cac2201844b211411.jsonl` и `runtime/logs/20261030T194248Z-5231742ee4ff4d99a2c094fa7312d64c.jsonl`.

Следующий шаг до spawn: пользователь выходит из игры, дожидается синхронизации и закрывает Steam; затем повторно выполняется малая проверенная копия сохранений, чтобы зафиксировать LOCAL character slot 1 и world slot 1. Только после `verified=true` можно отдельно согласовывать первый spawn.

## 2026-10-30 — Проверенная копия LOCAL-набора до spawn

- Пользователь закрыл игру и Steam после создания LOCAL character/world. Проверено отсутствие процессов `enshrouded`, `enshrouded_server`, `steam`, `steamwebhelper`.
- Вторая малая копия создана в `C:\Enshrouded-ai-companion\runtime\backups\20261030T194446Z-778186bd`.
- Манифест: `C:\Enshrouded-ai-companion\runtime\backups\20261030T194446Z-778186bd\manifest.json`; `mode=completed`, `verified=true`.
- Скопировано **144 файла, 30 613 580 байт** из полного Steam save root приложения 1203620 и полного локального `Saved Games\keen games\Enshrouded`.
- Встроенная тройная SHA-256-проверка прошла. Независимо повторно прочитаны все 144 источника и копии: **144 совпадения, 0 ошибок**, общий размер совпал.
- Локальная исходная точка теста присутствует в копии:
  - `local_saves\default\character0.ksd`, 1 878 байт, SHA-256 `0ef98058b8f9080d3560558f45fd8183c3f6087e5269f6bb2144e73ba0cc657f`;
  - `local_saves\default\world0.ksd`, 87 937 байт, SHA-256 `b6483f9e72901f88af9822034662be34ae0733d06d910684a63d09925de32faf`.
- `local_saves\default\global.ksd` отсутствует и в источнике: файл не был пропущен. Копия является точным снимком существующего набора, который игра успешно загрузила до spawn.
- Игра не запускалась повторно, spawn и другие команды тела не выполнялись.
- Перед публикацией документации повторно выполнены полный suite (**87 тестов PASS**), `compileall`, dry-run backup-конфигурации с текущими 144 файлами и `git diff --check`: PASS.

Резервная точка перед первым spawn готова. Следующий шаг — отдельное согласование первой команды `spawn` для мира `AI Body Test` / LOCAL world slot 1 и персонажа `Body Test` / LOCAL character slot 1.

### Публикация результатов подготовки

- Документация установки/первого запуска, полная история read-only диагностики и `config/first-test-saves-backup.json` опубликованы в `origin/master`.
- Основной коммит: **`e237c5b` — Record EMF installation and verified local test setup**; push `78badab..e237c5b` подтверждён GitHub.
- В коммит вошли только `README.md`, `docs/FIRST_RUN.md`, `docs/PROGRESS.md` и конфигурация backup. `runtime/` с сохранениями/логами, `artifacts/`, `dist/` и бинарники EMF остаются исключёнными из Git.
- Эта запись о результате push сохраняется следующим отдельным журнальным коммитом.

## 2026-10-30 — Этап 5: офлайн-подготовка первого игрового испытания

- Прочитаны актуальные правила и документы этапа. Сценарий ограничен LOCAL-миром `AI Body Test` slot 1 и LOCAL-персонажем `Body Test` slot 1; перед первым `spawn` требуется отдельное явное подтверждение пользователя.
- Steam и Enshrouded закрыты. Игра не запускалась, команды изменения игрового состояния не отправлялись, NPC не создавался.
- Повторная проверка копии `runtime/backups/20261030T194446Z-778186bd`: `verified=true`, 144 файла, 30 613 580 байт; SHA-256 всех исходников и копий совпали, ошибок 0.
- Установленные `dinput8.dll` (`53b3f6eb...f6dbee`) и `emf_core.dll` (`3b2b3ddd...417f3`) совпадают с аудитом EMF 0.3.2. Хеши установленных `main.lua` и `body.lua` совпадают с текущим адаптером. `runtime.lock` не найден.
- Конфигурация EMF включает только `lua` и `aic_body`; остальные моды отключены. Последний журнал подтверждает прежнюю успешную загрузку `aic_body`, но новая игровая сессия ещё не проверена.
- Создан игнорируемый Git постоянный профиль `runtime/personality.json` с именем `Спутник`; игрового entity ID в нём нет.
- `.tools/python/python.exe -m unittest discover -s tests -q`: **87 тестов PASS**.
- Создан [FIRST_INGAME_TEST.md](FIRST_INGAME_TEST.md). Все игровые этапы отмечены `NOT_TESTED`; визуальные проверки не заявлены выполненными.
- Следующий шаг: пользователь вручную запускает Steam и Enshrouded, выбирает LOCAL-персонажа `Body Test`, загружает LOCAL-мир `AI Body Test` и сообщает о полной загрузке. Затем выполняются только read-only `diagnose/status`; при успешном preflight запрашивается отдельное подтверждение непосредственно перед единственным `spawn`.

### Runtime preflight первой игровой сессии

- Пользователь вручную загрузил тестовый мир. Read-only `diagnose/status` успешно подключились к Python Bridge.
- Подтверждены EMF 0.3.2, API 20, protocol 1, client build 1273043; LOCAL-мир `AI Body Test` slot 1 и LOCAL-персонаж `Body Test` slot 1.
- `lua` 1.9.0 загружен, `aic_body` 0.1.0 загружен как script, остальные моды отключены.
- Состояние перед первым изменением: `mode=absent`, `orphaned=false`, `recovery_required=false`, `uncertain_spawn=false`, `safety_revision=2`, identity invalidation отсутствует.
- Epoch: `895d68a8425ad96d-1-table000001A9B2792FF00001000000`.
- Первоначальный Windows `error 5` относился к доступу ограниченной оболочки Codex к именованному каналу; повторные read-only запросы с разрешённым доступом прошли. Игровой сбой не зафиксирован.
- Следующий шаг: получить отдельное явное подтверждение пользователя и только после него отправить ровно один `spawn` через штатный Python CLI. Автоматический повтор запрещён.

### Результат первого spawn

- Пользователь отдельно подтвердил первый `spawn`. Через штатный Python CLI ровно один раз отправлен request ID `stage5-spawn-20261030T1956Z` в ранее проверенной сессии/epoch.
- EMF вернул entity ID 6854, после чего адаптер не смог получить fingerprint: `status=failed`, `code=fingerprint_missing`, `state_confirmed=false`.
- Итоговое состояние: `body_trusted=false`, `mode=recovery_required`, `recovery_required=true`, `uncertain_spawn=false`, `recovery_action=dismiss`. Read-only status по тому же request ID подтвердил результат.
- Защитный `runtime.lock` v2 существует и содержит текущий epoch; вручную не изменялся и не удалялся.
- Повторный spawn, `follow` и `stay` не выполнялись и запрещены. Неподтверждённая сущность по ID не удалялась. Исправления адаптера до фиксации результата первого теста не вносились.
- Следующий шаг: получить визуальный результат от пользователя — виден ли NPC и проявляет ли враждебность. После этого определить безопасное recovery-продолжение по протоколу.

### Визуальный результат и безопасная остановка

- Пользователь подтвердил: NPC появился враждебным, атаковал и убил тестового персонажа; затем персонаж возродился. Скриншот показывает Vukah первого уровня с красной полосой здоровья и враждебным индикатором рядом с персонажем; служебная бочка не видна. Скриншот в Git не добавляется. `spawn` — **FAIL**.
- Read-only status после возрождения сохранил `fingerprint_missing`, entity ID 6854, `body_trusted=false` и `recovery_required=true`. Защитный lock остаётся на месте.
- `follow`, `stay`, повторный `follow`, новый `spawn` и удаление сущности по неподтверждённому ID не выполнялись.
- Recovery-`dismiss` не отправлялся: без fingerprint он не имеет права уничтожить тело, а после переноса игрока при возрождении отсутствие ID среди активных ECS-сущностей не было бы достаточным доказательством очистки сохранения.
- Сценарий остановлен безопасно. Требуется штатно закрыть игру, затем отдельно согласовать offline-восстановление только тестовых LOCAL character/world из проверенной pre-spawn копии. До такого разрешения сохранения и lock не изменяются.

### Подготовка offline-восстановления

- Пользователь закрыл Enshrouded; процессы `enshrouded`/`enshrouded_server` отсутствуют.
- С pre-spawn копией расходятся `character0.ksd`, `world0.ksd` и две ротационные копии мира. Дополнительно созданы четыре ротационные копии персонажа, которых не было в manifest.
- Перед любым восстановлением текущие восемь тестовых файлов и `runtime.lock` скопированы в `runtime/recovery/stage5-failed-20261030T1958Z`. Диагностический снимок содержит 9 файлов; повторная SHA-256 проверка — ошибок 0. Каталог исключён из Git.
- План после отдельного разрешения: заменить четыре изменённых файла проверенными pre-spawn копиями, удалить только четыре появившиеся после теста ротационные копии персонажа, сверить весь LOCAL-набор с manifest и лишь после полного совпадения переместить активный lock в диагностический архив. Основные/Steam-backed сохранения не затрагиваются.

### Восстановление и итог этапа 5

- Пользователь отдельно подтвердил offline-восстановление. Первая попытка после замены четырёх основных файлов безопасно остановилась на неверной проверке пути диагностической копии; удаление новых backups и перемещение lock ещё не начинались. Проверка исправлена без изменения состава операции, после чего восстановление продолжено.
- Восстановлены четыре изменённых файла и удалены четыре ротационные копии персонажа, созданные тестом. Все 19 LOCAL-файлов совпали с pre-spawn manifest; ошибок 0, лишних файлов 0.
- После успешной полной сверки `runtime.lock` перемещён в игнорируемый Git диагностический архив. Активного lock в каталоге мода нет. Steam-backed и основные сохранения не изменялись.
- Фактический итог: `emf.spawn` создаёт `Enemy_Vukah_Melee` и возвращает ID, но обязательный fingerprint недоступен (`fingerprint_missing`). Поэтому код не дошёл до смены faction; Vukah появился враждебным и убил игрока. `follow`, `stay`, повторный `follow` и штатный `dismiss` — **BLOCKED/NOT VERIFIED**.
- Защитные механизмы сработали: повторного spawn и команд поведения не было, недоверенный ID не удалялся, recovery и lock сохранялись до подтверждённого offline restore.
- Требуется отдельное исправление: диагностировать отсутствующую часть fingerprint, найти подтверждённый идентификатор для Vukah либо сменить body после отдельного решения, а также исключить активного врага при раннем отказе без ослабления идентификационной защиты. Переход к Brain/голосу/навыкам заблокирован.
- После восстановления запущены проверки проекта: **87 тестов PASS**, `compileall` PASS, `git diff --check` PASS.
- Отчёт первого игрового испытания и журнал отправлены в `origin/master`: **`7e05f17` — Record first in-game body test failure**, push `e351ff8..7e05f17` подтверждён GitHub. Сохранения, диагностический снимок, runtime-логи, скриншот и бинарники в коммит не вошли.

## 2026-10-30 — Этап 6: исследование человекоподобного тела

- Перед работой ветка `master` была чистой и совпадала с `origin/master` на `159fa9e`. Прочитаны отчёт первого теста, protocol/test docs, Lua/Python-код и локальные pinned sources EMF `08d6001` / Enshwick `1355611`.
- Исследованы варианты A/B/C. Рекомендован долгосрочный вариант C: штатный workshop survivor как человеческое визуальное/физическое тело плюс отдельные Movement/Combat/Interaction/Inventory/Equipment controllers. Runtime spawn остаётся **BLOCKED**.
- Enshwick даёт 18 реальных workshop survivor template GUID/npcId. Для build 1273043 подтверждено движение уже существующего active NPC через `NpcCommandEvent.GoToPosition`, но direct spawn, исходная faction, ownership, combat и безопасный dismiss независимого экземпляра не подтверждены. Движок сохраняет одного entity на survivor, duplicate uniqueness может удалить сущность; все villager templates имеют `ForceSave`.
- Player clone без второго клиента/account authority не подтверждён. Наличие структур `PlayerInput`, `Inventory`, `Equipment` и `VisualEquipment` само по себе не делает spawnable player entity.
- Inventory API и игровые транзакции существуют; ItemId и pide/gear semantics исследованы. Безопасный долговременный inventory survivor, атомарный transfer/escrow и equip path для NPC не подтверждены, поэтому item mutations не реализованы.
- Созданы [HUMAN_COMPANION_RESEARCH.md](HUMAN_COMPANION_RESEARCH.md) и [HUMAN_COMPANION_ARCHITECTURE.md](HUMAN_COMPANION_ARCHITECTURE.md) с кандидатами, evidence-статусами, вариантами, lifecycle, capabilities и планом read-only survey.
- Добавлен офлайн-модуль `companion/human_body.py`: закреплённый каталог 18 кандидатов, `runtime_enabled=false`, capability contract и fail-closed `IdentityGate`. Gate требует ожидаемый model GUID и три полных последовательных наблюдения; missing/partial/reflection/timeout/identity change запрещают trust/delete.
- Vukah GUID и marker GUID вынесены из generic lifecycle в `mods/aic_body/body_profiles.lua` как `legacy_vukah`; protocol 1 / safety revision 2 и поведение старого адаптера не ослаблены. Пакет обновлён на пять Lua-файлов.
- Добавлено 10 тестов Human Body; все прежние 87 сохранены. Полный suite: **97 тестов PASS**. `compileall`, упаковка и `git diff --check`: PASS. SHA-256 `dist/aic_body-0.1.0.zip`: `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`.
- Все 18 записей локального каталога программно побайтно сопоставлены с pinned `WORKSHOP_SURVIVORS` (key, npcId, staff GUID, template GUID): **18 совпадений, 0 расхождений**. Две последовательные упаковки дали одинаковый SHA-256.
- Обновлены README, PROTOCOL, TEST_PLAN и TEST_RESULTS. Исторический [FIRST_INGAME_TEST.md](FIRST_INGAME_TEST.md) не изменялся.
- Игра не запускалась, spawn/игровые события не выполнялись, файлы игры и сохранения не менялись. Следующий шаг — отдельное согласование read-only survey `hunter_assistant` и `blacksmith_assistant`; human spawn до его результатов запрещён.
- Основной результат этапа 6 отправлен в `origin/master`: **`bb6c879` — Research human companion body architecture**, push `159fa9e..bb6c879` подтверждён GitHub. Бинарники, сохранения, runtime и приватные логи в коммит не вошли.


## 2026-10-30 — Этап 7: второй игровой персонаж как тело AI Companion

- Перед началом `master`, `origin/master` и `HEAD` совпадали на `141ee9f`; рабочее дерево было чистым. Прочитаны обязательные отчёты этапов 5/6 и текущие Lua/Python-модули.
- Исследованы pinned EMF `08d600155fcadc8e45cc9c6f3932a67c717345be`, Enshwick `135561192969af9ec9ffd0957b97ca6a7aa31820`, SDK официального EMF 0.3.2 и официальные материалы Enshrouded/Steam.
- Вариант A (второй полноценный player без клиента) классифицирован `UNSUPPORTED`: EMF умеет получить локального/подключённых игроков и spawn template entity, но не создаёт player slot, network peer, account authority и не загружает второй character save в сессию.
- Вариант B классифицирован `UNKNOWN`: визуальная/NPC-копия может быть резервным телом, но не является настоящим player и не получает автоматически штатные inventory/equipment/skills/save semantics. Результаты этапа 6 сохранены без переписывания.
- Вариант C классифицирован `LIKELY` и рекомендован как единственный реалистичный путь к настоящему игровому персонажу. Штатный второй client даёт account/slot/entity и character persistence, но AI-control channel, работа двух клиентов на одном ПК и производительность не подтверждены.
- Официальные правила Steam требуют отдельный account и доступную отдельную копию для одновременной игры. Обход авторизации/лицензии не исследовался и не предлагался.
- Read-only перечисление подтвердило отдельные LOCAL `character0.ksd/world0.ksd` и Steam remote character/world slots. Содержимое сохранений не редактировалось и не публиковалось; Steam ID исключён из документации.
- При privacy-review найден числовой Steam user ID в ранее отслеживаемых `STAGE3_PREFLIGHT.md`, `PROGRESS.md` и двух backup-конфигурациях; все записи заменены на `<SteamUserID>`. Конфигурации теперь требуют локально подставить ID перед будущим запуском backup; исторические технические результаты не изменены.
- Созданы [PLAYER_CHARACTER_COMPANION_RESEARCH.md](PLAYER_CHARACTER_COMPANION_RESEARCH.md) и [PLAYER_CHARACTER_COMPANION_ARCHITECTURE.md](PLAYER_CHARACTER_COMPANION_ARCHITECTURE.md): ECS, saves, A/B/C, inventory/equipment, authority, интерфейс команд, риски и безопасный план следующего этапа.
- Добавлен офлайн-модуль `companion/player_character.py`: evidence-каталог вариантов и команд, проверка distinct host/companion account, session token, player slot/entity, network peer и обязательных компонентов. Даже trusted identity не включает runtime-control; неподтверждённые операции fail closed.
- Добавлено 13 тестов: классификация, отсутствие runtime API, разделение основного персонажа/companion, ownership, missing components, disconnect, session/account/slot/entity changes, unknown network authority и отказ придуманным операциям.
- Полный suite: **110 тестов PASS**; `compileall` PASS. Пакет пересобран дважды, обе сборки: SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`.
- Ограничение: игровой тест этапа 7 не выполнялся. Игра и второй client не запускались, spawn/input/inventory не выполнялись, файлы игры и сохранения не изменялись.
- Следующий шаг после отдельного разрешения: подготовить read-only Host Observer, отдельный test account/character и проверенные backups; пользователь вручную подключает второй client. Сначала подтверждаются два разных account/slot/entity и штатное сохранение, затем отдельно исследуется один безопасный input только второго процесса.


## 2026-10-30 — Публикация этапа 7

- Основной результат этапа 7 опубликован в `origin/master`: **`f62b303` — Research player-character companion architecture**, push `141ee9f..f62b303` подтверждён GitHub.
- В коммит вошли офлайн policy-модуль, 13 тестов, два новых отчёта и обновления README/test/progress docs. Сохранения, игровые бинарники, runtime-логи и Steam user ID не вошли.
- Игра и второй client не запускались; runtime-control остаётся заблокированным до отдельного разрешения и read-only испытания.

## 2026-10-30 — Этап 8: независимый человекоподобный NPC

- Перед работой `master` был чистым и совпадал с `origin/master` на `1e9215a`; выполнен `git fetch origin master`. Прочитаны правила, документы этапов 5–7, текущий Lua/Python и pinned EMF/Enshwick.
- Решение со вторым игровым клиентом отклонено. Целевая архитектура: один Enshrouded/account/player и отдельный Human NPC Body Adapter, независимый от Brain и personality UUID.
- В pinned данных не найден подтверждённый non-unique ordinary human template. Все villager templates с `ActiveNpcState` проходят uniqueness по template GUID и имеют `ForceSave`; 18 workshop survivor descriptors остаются unique story NPC и не могут служить независимым телом.
- Public EMF Lua подтверждает spawn существующего template GUID и read-only template components, но не регистрацию нового entity template. Shared template model/animation write затронул бы все экземпляры; безопасной instance-local замены не найдено. EML data patch отмечен upstream как необходимый путь для нового villager GUID, но его готовый безопасный API/формат для проекта не подтверждён.
- Созданы [INDEPENDENT_HUMANOID_RESEARCH.md](INDEPENDENT_HUMANOID_RESEARCH.md) и [INDEPENDENT_HUMANOID_ARCHITECTURE.md](INDEPENDENT_HUMANOID_ARCHITECTURE.md). Зафиксированы identity/ownership, lifecycle, recovery, movement/combat/inventory/equipment и точный следующий read-only этап.
- Добавлен `companion/independent_humanoid.py`: `HumanBodyDescriptor`, evidence-aware capabilities, uniqueness checks и fail-closed lifecycle. Unknown/unique/missing resources/faction/ownership/dismiss блокируют preflight; uncertain spawn/reload/identity change блокируют повтор и cleanup неподтверждённой сущности.
- Подготовлен выключенный read-only `mods/aic_humanoid_survey`: он читает существующих nearby active NPC и сообщает model/animation/faction/components. Public Lua не выдаёт template GUID, поэтому мод явно возвращает `template_guid_available=false`.
- Полный suite: **126 тестов PASS**; `compileall` PASS. Игра не запускалась, мод не устанавливался, spawn/faction/destroy/inventory/save operations не выполнялись.
- Runtime humanoid остаётся **BLOCKED**. Следующий шаг требует отдельного разрешения: backup LOCAL save и read-only survey существующего `hunter_assistant`. После него — отдельное исследование нового EML template; прямой spawn story survivor запрещён.

## 2026-10-30 — Публикация этапа 8

- Основной результат этапа 8 опубликован в `origin/master`: **`69b502a` — Research independent humanoid companion body**, push `1e9215a..69b502a` подтверждён GitHub.
- В коммит вошли только исходники offline gate/read-only survey, тесты и документация. Сохранения, runtime-логи, архивы и бинарники не публиковались.
- Игра не запускалась, survey не устанавливался, игровой spawn не выполнялся.
## 2026-10-30 — Этап 9: собственный Humanoid Template через EML

- До работы `master`, `origin/master` и HEAD совпадали на `cb44c3c`; рабочее дерево было чистым. Прочитаны правила, отчёты этапов 5–8, protocol/test docs и текущие Lua/Python модули.
- Получен официальный source EML/KFC parser `Brabb3l/kfc-parser`, tag 0.2.0, commit `16708594d686b030d909f2d835b199d879ea9ad8`, GPL-3.0. Установка и запуск EML не выполнялись; checkout находится в ignored `.research/`.
- Исходники EML подтверждают настоящий `create_resource` с новым/fixed GUID, duplicate rejection, reflected typed resource mutation и запись новых resources. Pinned EMF `make_mod.py` подтверждает практический clone нового `keen::ecs::TemplateResource`, component edits и условную регистрацию GUID.
- Установлено: EML и EMF — независимые loaders; EML патчит asset data до загрузки, EMF управляет runtime entity. Совместный runtime build 1273043 + EML 0.2.0 + EMF 0.3.2 ещё не испытан.
- Создан реальный offline EML patch `experimental/eml_humanoid`: clone `hunter_assistant` в fixed GUID `a1c90001-5e4d-4a91-8a1c-000000000001`, новый FNV-1a `npcId=2939921867`, initial `PlayerAlly`, fail-closed assertions и conditional GuidRegistry registration. Source story resource не меняется; autospawn/runtime/save/inventory операций нет.
- Добавлен `companion/eml_humanoid.py`: immutable descriptor, fixed GUID catalog/FNV verification, structural validator и runtime gate. `runtime_enabled=false`; model/animation GUID, creation marker, ownership и safe dismiss остаются неподтверждёнными. Старый spawn allow-list и IdentityGate не ослаблены.
- Созданы `EML_HUMANOID_TEMPLATE_RESEARCH.md` и `EML_HUMANOID_TEMPLATE_ARCHITECTURE.md`; обновлены README, TEST_PLAN и TEST_RESULTS. История этапов 5–8 не переписывалась.
- Добавлено 15 tests. Полный suite: **141 PASS**; `compileall`, Lua checks через Lupa и `git diff --check`: PASS. Системного `lua/luac` нет, что явно зафиксировано.
- Игра не запускалась, EML не устанавливался, игровые файлы/сохранения не менялись, spawn/faction/destroy/inventory runtime не выполнялись.
- Вердикт: новый human TemplateResource технически возможен и offline prototype корректен по подтверждённому EML API. Runtime остаётся **BLOCKED** до раздельных испытаний: сначала patch-load/read-only fingerprint, затем — после нового разрешения — один контролируемый spawn. Главные блокеры: совместная загрузка EML/EMF, точные model/animation/components, workshop/ForceSave behavior, instance marker/ownership и safe dismiss.
- Следующий практический шаг: отдельное согласование эксперимента patch-load only с проверенным EML 0.2.0 binary, backup/restore отдельного LOCAL test world и read-only observer; первый spawn с ним не совмещать.

## 2026-10-30 — Публикация этапа 9

- Исследование, offline EML patch, descriptor, 15 новых тестов и документация опубликованы в `origin/master`: **`315b1ec` — Research EML humanoid template prototype**, push `cb44c3c..315b1ec` подтверждён.
- Опубликованы только исходники и Markdown. EML/game binaries, сохранения, runtime-логи и приватные идентификаторы в коммит не вошли.

## 2026-10-31 — Этап 10: подготовка загрузки собственного Humanoid Template

- Прочитаны правила проекта и результаты этапов 3/9. Фаза A выполнена; фаза B не выполнялась: игра не запускалась, EML не устанавливался, файлы игры/KFC/DAT/сохранения не изменялись, spawn/destroy/faction/inventory команды не вызывались.
- Проверен официальный EML 0.2.0 release `Brabb3l/kfc-parser` tag/commit `16708594d686b030d909f2d835b199d879ea9ad8`. Скачанные в ignored audit-каталог `dbghelp.dll` и `emm.exe` совпали с GitHub SHA-256, не запускались, оказались x64 PE32+ без Authenticode. Defender custom scan прошёл без детектов; защита не отключалась. Воспроизводимая пересборка и GitHub attestation отсутствуют.
- Зафиксирована схема совместной установки: EMF остаётся `dinput8.dll`; EML использует только `dbghelp.dll`; альтернативный EML `dinput8.dll` запрещён. Имена не конфликтуют, но совместный runtime start двух proxy остаётся непроверенным.
- Patch `experimental/eml_humanoid` дополнен capability `export`, повторным EML lookup созданного resource, fingerprint model/animation/components/faction/npcId, проверкой неизменности source и положительным маркером `AIC_EML_TEMPLATE_READY`. Он по-прежнему не содержит spawn/runtime/save/inventory операций.
- Добавлен выключенный по умолчанию read-only `mods/aic_template_observer` с командами `status`, `inspect`, `compare`. Observer читает evidence, не мутирует игру и явно возвращает `direct_emf_template_lookup=UNAVAILABLE_WITHOUT_ENTITY`.
- Добавлены fail-closed `companion/stage10.py` и read-only CLI `scripts/stage10.py`: exact hashes/build/path, conflict/stale checks, verified backup, install receipt, partial-install rollback и отдельно проверяемое восстановление KFC/resources. Mutation helpers требуют закрытой игры; EML/patch/observer перепроверяются непосредственно перед будущей установкой. Все операции по умолчанию dry-run.
- Фактический preflight установленной игры: PASS для build `1273043`, EXE SHA-256 `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882`, EMF `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee`, EML `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa`; baseline DAT `000`–`054`; `phase_b_allowed=false`.
- Backup выполнен только как dry-run: 20 файлов, 224 556 422 байта. Реальная verified backup не создавалась.
- Добавлены 22 теста Stage 10. Целевой Stage 9+10 прогон: **37 PASS**. Полный suite: **163 PASS**; `compileall`: PASS. Проверены неправильный loader/stale evidence, системное определение running game с fail-closed ошибкой, malformed evidence, writer finalization, partial/repeated install, corrupt backup, changed rollback file и неизвестные DAT.
- Документация: `EML_EMF_COMPATIBILITY.md`, `STAGE10_TEMPLATE_LOAD_PLAN.md`, `STAGE10_TEMPLATE_LOAD_RESULTS.md`, а также README/TEST_PLAN/TEST_RESULTS обновлены. Бинарники EML, игра, сохранения и runtime-логи не войдут в Git.
- Блокер: public EMF Lua предоставляет `world:template(component, entity)`, но не read-only lookup/enumeration `TemplateResource` по GUID. Без запрещённого spawn observer не может независимо подтвердить новый resource. Вердикт **BLOCKED_BEFORE_PHASE_B_FULL_CRITERIA**.
- Следующий шаг: подтвердить/реализовать native read-only EMF lookup либо явно изменить критерий на EML evidence + успешный game load + EMF observer/bridge. До решения установка и фаза B не запрашиваются.

## 2026-10-31 — Публикация этапа 10

- Подготовка load-only проверки, fail-closed инструменты, 22 новых теста и документация опубликованы в `origin/master`: **`e5ef303` — Prepare EML humanoid template load audit**, push `26ae31a..e5ef303` подтверждён GitHub.
- В публикацию вошли только исходники, тесты и Markdown. EML/game binaries, KFC/DAT/KSD, сохранения, runtime-логи и приватные данные не публиковались.
- Фаза B не выполнялась и остаётся заблокированной полным критерием прямого EMF lookup.

## 2026-10-31 — Этап 10.1: acceptance gate load-only

- Пользователь явно пересмотрел критерий: прямой EMF lookup остаётся `UNAVAILABLE_WITHOUT_ENTITY`, но не блокирует load-only проверку. Успех теперь разделён на A=`EML_PATCH_APPLIED`, B=`GAME_LOAD_CONFIRMED`, C=`EMF_RUNTIME_CONFIRMED`.
- В `companion/stage10.py` добавлен вычисляемый evaluator со статусами `NOT_EXECUTED`, `PREPARATION_READY`, `PARTIAL_SUCCESS`, `LOAD_ONLY_SUCCESS`, `FAILED`, `RECOVERY_REQUIRED`. Отсутствующие данные остаются `null/UNKNOWN`; `spawn_ready` всегда `false`.
- Для корреляции одного запуска будущая установка генерирует случайный 128-битный `run_token`, внедряет его в EML patch и observer и сохраняет в install receipt. EML evidence/marker, EMF marker/observer replies и отчёты должны содержать тот же token; timestamp отдельно не принимается.
- Repository patch и observer содержат placeholder и fail-closed assertions. Ручная установка без штатной подстановки token не считается доказательством и не должна загрузиться.
- CLI разделён на read-only `scripts.stage10 preflight` и `evaluate`. Preflight сообщает binaries/patch/observer/backup/install readiness и blockers. Evaluate принимает только собранные logs/evidence/JSON/manifest, не запускает игру и не изменяет файлы.
- Observer сохраняет `status`, `inspect`, `compare`, отмечает источник `EML_EXPORT`, runtime-факт `EMF_RUNTIME` и ограничение `UNAVAILABLE_WITHOUT_ENTITY`; spawn/faction/ECS/inventory/destroy/save writes отсутствуют.
- Добавлен [STAGE10_1_ACCEPTANCE_CRITERIA.md](STAGE10_1_ACCEPTANCE_CRITERIA.md); обновлены README, compatibility, plan/results и test docs. Исторические результаты реального Vukah и этапов 9/10 не переписывались.
- Добавлено 19 тестов: полный synthetic A/B/C, writer/stale/mismatch/fingerprint/observer/bridge/game/files/saves/backup/rollback failures, корреляция сегментов журналов и реального tab-separated Lua marker, direct lookup limitation и вечный запрет spawn. Все прежние 163 сохранены; полный suite **182 PASS**, `compileall` и `git diff --check` PASS.
- Реальный read-only preflight установленной игры: `PREPARATION_READY`; exact build/game/EMF/EML hashes, patch и observer PASS. Новый backup отсутствует, поэтому `installation_ready=false`, blocker `verified_backup_missing`, `phase_b_allowed=false`.
- Текущий backup dry-run повторно насчитал 20 файлов / 224 556 422 байта. Реальная копия не создавалась.
- Игра не запускалась, EML не устанавливался, DLL/KFC/DAT/KSD/saves не менялись, runtime artifacts A/B/C не создавались, spawn не выполнялся. Текущий evaluator без входов: `NOT_EXECUTED`.
- Следующий шаг требует отдельного разрешения пользователя: создать и проверить новый backup, установить только EML/patch/observer, затем пользователь вручную выполняет load-only запуск LOCAL `Body Test` / `AI Body Test` без spawn.

## 2026-10-31 — Публикация этапа 10.1

- Пересмотренный acceptance gate, корреляция `run_token`, read-only CLI `preflight/evaluate`, 19 новых тестов и документация зафиксированы основным коммитом **`144af38` — Revise template load acceptance gate**.
- Перед публикацией полный suite: **182 PASS**; целевой Stage 9/10/10.1 suite: **56 PASS**; `compileall` и `git diff --check`: PASS.
- В Git включены только исходники, тесты и Markdown. DLL, EML/game binaries, KFC/DAT/KSD, сохранения, runtime evidence и приватные журналы не публикуются.
- Игровые действия не выполнялись. Текущий runtime-результат остаётся `NOT_EXECUTED`; verified backup ещё не создан, поэтому установка и фаза B ожидают отдельного разрешения пользователя.

## 2026-10-31 — Этап 10.2, часть A: read-only preflight

- ТЗ этапа 10.2 прочитано как трёхчастная процедура. Выполнена только разрешённая часть A; отдельного разрешения на backup/установку нет. Игра не запускалась, EML не устанавливался, игровые файлы и сохранения не менялись.
- Усиленный фактический preflight: `PREPARATION_READY`; build `1273043`, EXE/EMF/EML SHA-256, patch и observer PASS. Enshrouded/server не запущены; `dbghelp.dll`, `eml.json`, `enshrouded.kfc.bak`, сторонние EML-моды, stale evidence, install temp/receipt и observer collision отсутствуют. DAT baseline `000`–`054`.
- На диске игры свободно 434 613 178 368 байт при минимуме preflight 1 297 670 144 байт. На проектном диске свободно 618 937 020 416 байт.
- Новый backup dry-run: 20 файлов / 224 556 422 байта, включая два KFC/resources и 18 файлов из LOCAL `default`. Там ровно один текущий character и world; связь с `Body Test` / `AI Body Test` ранее подтверждена пользователем, но KSD офлайн не декодируется.
- Старые backups этапов 3/5 не совместимы с manifest Stage 10 и не будут переиспользованы. Исправлен fail-closed дефект `verify_backup`: legacy `entries`-mapping больше не вызывает `AttributeError`, а возвращает `False`.
- Preflight расширен проверками `eml.json`, KFC `.bak`, сторонних EML-модов, observer config, install temporary/receipt и свободного места. План содержит ровно 9 install files. Dry-run install без нового backup остановлен `verified_backup_required`; rollback без receipt — `rollback_receipt_invalid`.
- Добавлены 2 теста; Stage 10 suite **24 PASS**, полный suite **184 PASS**, `compileall` и `git diff --check` PASS. Пустой evaluator повторно вернул `NOT_EXECUTED`. Runtime A/B/C, новый resource, game load, evidence, save integrity и rollback остаются `NOT_EXECUTED`; `spawn_ready=false`.
- Создан [STAGE10_2_RUNTIME_RESULTS.md](STAGE10_2_RUNTIME_RESULTS.md). Следующий шаг требует отдельного явного разрешения пользователя на часть B: создать verified backup и установить EML/patch/observer; затем остановиться до ручного запуска игры.

## 2026-10-31 — Публикация этапа 10.2, части A

- Read-only preflight, усиленные fail-closed проверки, 2 regression tests и технический отчёт зафиксированы основным коммитом **`40d08af` — Prepare stage 10.2 load test preflight**.
- Перед публикацией полный suite **184 PASS**, Stage 10 suite **24 PASS**, `compileall`, Lua validation и `git diff --check` PASS.
- Публикуются только исходники, тесты и Markdown. Игра, EML/EMF binaries, backup, KFC/DAT/KSD, сохранения, install receipt и приватные runtime-журналы не входят в Git.
- Часть B не выполнялась. Статус остаётся `PREPARATION_READY`, runtime evaluator — `NOT_EXECUTED`; следующий шаг ожидает отдельного разрешения пользователя.

## 2026-10-31 — Этап 10.2, часть B: backup и установка

- Пользователь отдельно разрешил создать verified backup и установить EML/humanoid patch/read-only observer без запуска игры. Перед изменениями повторный preflight PASS; Enshrouded/server закрыты, hashes/build/conflicts повторно проверены.
- Создан `stage10-pre-eml-20261030T220012Z`: 20 файлов / 224 556 422 байта. Manifest `verified=true`; 20/20 backup hashes и повторные hashes текущих источников совпали, mismatch 0. Старые backups не использовались.
- Установлены ровно 9 файлов из существующего install plan. Receipt `complete`; run token `69a6a5ff13e66c37614e212790464271`; 9/9 hashes совпали. Токен внедрён в patch/observer, install placeholders отсутствуют, repository placeholders сохранены.
- `dbghelp.dll` и неизменный `dinput8.dll` совпадают с закреплёнными SHA-256. `eml.json` включает export и выключает console. Observer включён отдельной INI. Временных install files, stale evidence и `enshrouded.kfc.bak` до первого запуска нет. Defender и real-time protection включены.
- `aic_body` не входит в receipt и не менялся. Выявлено предварительно существовавшее legacy-состояние: установленный `body.lua` старше текущей repository-версии с `body_profiles.lua`, тогда как `main.lua` совпадает. Это не исправлялось; spawn и `aic_body.request` запрещены.
- Создан ignored pre-run baseline install/manifest hashes, game root и metadata 55 DAT. Игра не запускалась; A/B/C, EML evidence, game load, save integrity и rollback остаются `NOT_EXECUTED`; `spawn_ready=false`.
- Текущая контрольная точка: **INSTALLATION_READY — WAITING_FOR_MANUAL_GAME_START**. Пользователь должен один раз вручную запустить Steam/Enshrouded, выбрать LOCAL `Body Test` / `AI Body Test`, загрузить мир без команд мутации и сообщить «загрузился».

## 2026-10-31 — Публикация этапа 10.2, части B

- Проверенные результаты backup/установки и статус ожидания ручного запуска зафиксированы коммитом **`55b6665` — Record stage 10.2 installation readiness**.
- Перед публикацией полный offline suite **184 PASS**, `compileall` и `git diff --check` PASS; процесс игры отсутствует.
- В Git вошёл только обезличенный технический отчёт. Backup/manifest, install receipt, pre-run baseline, токенизированные Lua-копии, DLL, KFC/DAT/KSD, сохранения и runtime-журналы остались в ignored runtime/игровом каталоге.
- Следующее действие принадлежит пользователю: один ручной запуск. Codex игру не запускал и spawn не выполнял.

## 2026-10-31 — этап 10.2, фактический load-only результат

- Пользователь вручную загрузил LOCAL `Body Test` / `AI Body Test`; Codex выполнил только read-only диагностику. Spawn и команды мутации не выполнялись.
- A=`false`: EML загрузил мод и применил 1 patch, но `model_guid=nil`; nil-подобный fingerprint теперь fail-closed.
- B=`true`: главное меню и LOCAL-мир загрузились, resource/game errors отсутствуют.
- C=`unknown`: EMF/Bridge/status/compare подтверждены, но `inspect` обрезан на 1023 байтах.
- Verified backup цел; все install hashes совпадают. DAT `000–054` не менялись; EML создал нулевые `055–063`, KFC backup/cache/export/logs. Неатрибутированных изменений нет.
- Итог `FAILED`, `load_only_success=false`, `spawn_ready=false`, `rollback_ready=true`, реальный rollback не выполнялся.
- Observer/evaluator исправлены для nil fingerprints, JSON-escaped tabs и компактного inspect. Полный suite: 188 PASS.

## 2026-10-31 — безопасный откат этапа 10.2

- Откат выполнен после отдельного явного разрешения пользователя; процесс Enshrouded до и после операции отсутствовал.
- `enshrouded.kfc` и `enshrouded.kfc_resources` восстановлены из verified backup и совпали с исходными SHA-256.
- Удалены только атрибутированные outputs: `enshrouded.kfc.bak`, DAT `055–063`, 9 файлов EML/patch/observer, `.cache`, `export`, `logs` и оставшиеся пустые каталоги patch.
- DAT `000–054` точно совпадают с baseline по именам, размерам и mtime. EMF `dinput8.dll` сохранил закреплённый SHA-256. Не осталось install/restore temporary files.
- LOCAL-сохранения не восстанавливались; их pre-run версии продолжают храниться в проверенном backup.
- Итоговая rollback verification: `ok=true`. Игра не запускалась, spawn не выполнялся. Этап 10.2 остаётся `FAILED`; повторная установка и новый запуск не разрешены.
## 2026-11-01 — Stage 10.6, часть A: EML Humanoid Clone Visual Verification

- Прочитаны результаты 10.2–10.5, текущие EML/observer/evaluator и KFC evidence. Исторический результат 10.2 сохранён.
- Patch обновлён до 0.3.0 и evidence `aic_eml_humanoid_evidence_v3`: source/clone GUID, npcId/faction, component fingerprint, все 11 typed полей `CharacterSetup`, animation/retarget, source integrity, registry, writer status и provenance.
- Создан canonical source baseline из Stage 10.5: 18 preset paths с ItemInfo/item/RenderModel/gender override, animation graph и hierarchy 102 joints. SHA-256 baseline `535732bda93e41ff3b3070e362d649b9c6875101826d2c1823c81945b22d8837`.
- Visual fingerprint обновлён до v2 с уровнями STRUCTURAL/CHARACTER_SETUP/REFERENCES/DEPENDENCIES/RUNTIME_RENDER. `ModelResource` и `RenderEquipment.lastModels` не требуются; runtime render остаётся UNKNOWN; `spawn_ready=false`.
- Добавлен fail-closed evaluator Stage 10.6 A/V/B/C. Observer 0.2.0 читает только evidence v3, коррелирует run token/hash и ограничивает ответ 1023 байтами. Spawn/entity/save mutation отсутствуют.
- Реальная среда проверена только чтением: Enshrouded не запущен; SHA-256 EXE/KFC/resources/EMF loader совпадают с baseline; после отката EML, observer и export отсутствуют.
- Добавлено 40 тестов Stage 10.6. Полный suite: **258 tests run: 257 PASS, 1 skip**; compileall и `git diff --check` PASS.
- KFC Inspector повторно собран из locked dependencies: **2 Rust tests PASS**. Реальный dry-run preflight вернул `PREPARATION_READY`; свободного места достаточно, единственный blocker — отсутствие нового verified backup.
- Созданы план, evidence contract и runtime report со статусом **NOT_EXECUTED**. Часть B не разрешена: новый backup не создавался, EML не устанавливался, игра/сохранения не менялись.
- Следующий шаг: отдельное разрешение пользователя на часть B — новый verified backup и установка без запуска игры.
- Checkpoint реализации опубликован в `origin/master`: `d8d843d` (`Prepare Stage 10.6 visual evidence verification`).

## 2026-11-01 — Stage 10.6, Phase B: verified backup и установка

- Пользователь отдельно разрешил Phase B. До backup, непосредственно перед установкой и после неё процессы `Enshrouded`/server отсутствовали. Игра не запускалась.
- Повторный preflight подтвердил build 1273043, закреплённые SHA-256 EXE/KFC/resources/EMF/EML, отсутствие конфликтов и install plan ровно из 9 файлов.
- Создан новый backup `stage10-6-pre-eml-20261101T083034Z`: **24 файла / 224 564 012 байт** (2 KFC + 22 LOCAL saves). Backup hashes и текущие source hashes совпали 24/24.
- Установлены EML, patch 0.3.0 и observer 0.2.0. Receipt `complete`; 9/9 post-install hashes совпали. Создан новый 128-bit run token; публично сохранён только SHA-256 `12161c78d96705d70edba23e1cb139b05adbc96ac40aa33155b891f3ae413a`.
- Placeholder отсутствует в установленных Lua; token внедрён в patch/observer ровно по одному разу. KFC и LOCAL saves установкой не менялись; pre-run baseline содержит 55 DAT и 22 saves.
- Rollback dry-run подтвердил все 9 файлов. WinDefend и SecurityHealthService работают; защита не отключалась и не перенастраивалась.
- Runtime A/V/B/C остаётся **NOT_EXECUTED**, `spawn_ready=false`: игра, EML runtime и NPC не запускались. Следующий шаг требует отдельного разрешения пользователя на Phase C.
- После hash-сверки найдено содержательное расхождение: runtime `mod.json`/Lua — 0.3.0/evidence v3, но установленный README остался с текстом 0.2.0/«не установлен». По условию пользователя дальнейшие установочные действия остановлены; игровой файл и receipt не исправлялись.
- Repository README исправлен, validator теперь отклоняет stale README, добавлен regression test. Текущий статус — **BLOCKED_POST_INSTALL_DOCUMENTATION_MISMATCH**; Phase C не готова до отдельного разрешения на remediation.
- После исправления исходников полный suite: **259 tests run: 258 PASS, 1 skip**; compileall и `git diff --check` PASS.
- Отчёт Phase B, исправленный repository README и regression-защита опубликованы в `origin/master`: `34fcc93` (`Record Stage 10.6 Phase B installation`).

## 2026-11-01 — Stage 10.6 Phase B remediation audit

- Пользователь разрешил заменить только installed README при обязательном безопасном update plan/receipt. Перед проверкой игра/server отсутствовали, backup verified, receipt `complete`, hashes совпали 9/9, rollback dry-run PASS.
- Штатный installer не имеет single-file update/revision операции: preflight остановился `conflicting_or_repeated_dbghelp_install`, install dry-run — `installation_collision:dbghelp.dll`. Ручное редактирование receipt запрещено условиями и не выполнялось.
- Установленный README, остальные 8 файлов, receipt, Lua/DLL/JSON, KFC/DAT/saves не менялись. Игра не запускалась, NPC не создавался.
- Итог: **BLOCKED_NO_SAFE_RECEIPT_UPDATE_MECHANISM**. Phase C не готова; следующий безопасный шаг требует отдельного разрешения на разработку атомарного update-механизма либо полный rollback/reinstall.
- Read-only remediation audit опубликован в `origin/master`: `b536271` (`Audit Stage 10.6 README remediation blocker`).

## 2026-11-01 — Stage 10.6 Phase B full rollback/reinstall remediation

- Пользователь отдельно разрешил полный контролируемый rollback и повторную установку исправленного plan. До, между мутациями и после операции `Enshrouded`/server отсутствовали; игра не запускалась.
- Перед rollback verified backup прошёл проверку 24/24; исходный receipt был `complete`, все 9/9 installed hashes совпали. Его SHA-256 сохранён неизменным для истории.
- Исправлен дефект штатной очистки: rollback теперь удаляет известный пустой `mods/aic_eml_humanoid/src` deepest-first. Добавлен regression test, подтверждающий сохранение посторонних файлов.
- Штатный rollback удалил ровно 9 путей receipt. После него backup, 55 DAT, 22 LOCAL saves, KFC/resources и EMF loader прошли integrity-проверку.
- Новый preflight прошёл; исправленный plan установлен с отдельным run token и отдельным receipt `state=complete`. Исправленный README 0.3.0 установлен; post-install hashes и rollback dry-run совпали 9/9.
- После установки backup 24/24, DAT 55/55 и LOCAL saves 22/22 повторно совпали по SHA-256. Неизвестные файлы и saves не удалялись и не изменялись.
- Полный suite: **260 tests run: 259 PASS, 1 skip**; compileall и `git diff --check` PASS.
- Статус: **PHASE_B_COMPLETE — READY_FOR_PHASE_C_REVIEW**. Phase C не запускалась и требует отдельного разрешения; A/V/B/C остаются `NOT_EXECUTED`, `spawn_ready=false`.
- Реализация, regression test и отчёты зафиксированы коммитом `6ec5e0c` (`Complete Stage 10.6 Phase B remediation`).

## 2026-11-01 — Stage 10.6 Phase C preflight

- Пользователь разрешил контролируемый load-only тест с ручным запуском игры и запретом spawn/entity/faction/inventory/save mutations. Rollback не разрешён.
- Read-only preflight выполнен при закрытых `Enshrouded` и server. Новый receipt `complete`, SHA-256 `d8ca5937f03663e7c9e1468890f1126be8e0dcad403bade47384c70d6a1aa15a`; установленные hashes совпали 9/9, rollback dry-run распознал 9/9.
- Verified backup прошёл проверку 24/24; текущие KFC/resources и все LOCAL source-файлы совпали с manifest. Baseline содержит 55 DAT и 22 LOCAL save-файла.
- Stale evidence, KFC `.bak`, EML cache/export/logs, bridge descriptor и `.stage10-install` отсутствуют. В EML `mods` находится только `aic_eml_humanoid`; прочие штатные EMF-моды выключены, кроме необходимых Lua/observer и защищённого от autospawn `aic_body`.
- Создана ignored preflight snapshot и подготовлен read-only collector с fail-closed проверкой LOCAL `Body Test` slot 1 / `AI Body Test` slot 1 до observer-запросов. Статус: **READY_FOR_MANUAL_START**, `spawn_ready=false`.

## 2026-11-01 — Stage 10.6 Phase C runtime и post-run

- Пользователь вручную запустил и закрыл Enshrouded. Bridge до observer-запросов подтвердил LOCAL character `Body Test`, slot 1, и LOCAL world `AI Body Test`, slot 1.
- EML применил patch 0.3.0 (`Applied 1 patches`) и создал evidence v3. Observer `status/inspect/compare` ответил без ошибок, с read-only/spawn-forbidden flags и совпадающим token/fingerprint. Команды spawn/faction/inventory/entity/save не выполнялись.
- Evaluator: **A=true, V=false, B=true, C=true**; verdict **FAILED — V:CHARACTER_SETUP**. Structure/81 components, animation graph, retarget, 18 references, dependency closure и source integrity прошли.
- Typed gate отклонил девять `HashKey32` полей: source/clone имеют `UNSUPPORTED` и пустые values. Только `gender` и `useNewProportions` подтверждены. `source_registered=false`, `registry_added=false`; независимый runtime template lookup не подтверждён.
- После закрытия процессы отсутствовали. Backup 24/24 и install 9/9 PASS; исходные DAT `000–054` совпали 55/55 по SHA-256, добавлены только нулевые `055–063`. KFC/resources изменены EML, KFC `.bak` совпал с baseline. LOCAL-набор сохранил 22 файла, штатно изменены 6; неизвестных изменений 0.
- Rollback readiness=true, но rollback по условию не выполнялся. `load_only_success=false`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
- Runtime evidence, integrity review и подробный Phase C report зафиксированы коммитом `d91569d` (`Record Stage 10.6 Phase C load-only results`).


## 2026-11-01 — Stage 10.7 Phase A: HashKey32 и registration

- Прочитаны Stage 10.6 результаты и закреплённые исходники EML/KFC commit `16708594d686b030d909f2d835b199d879ea9ad8`. Причина девяти `UNSUPPORTED` подтверждена: reflected `HashKey32` — `MappedStructValue` userdata; старый Lua разворачивал `.value` только у table. Вложенный UInt32 EML отдаёт точным Lua integer.
- Из проверенного KFC baseline подтверждены все девять source values hunter: voice `3178345104`, preset `1602195472`, hair `100818570`, beard `0`, hair/beard color `2593349132`, skin `510686028`, eyebrow `1294605571`, eye `1843389514`. Runtime equality source/clone новым accessor ещё не выполнялась.
- Подготовлен patch 0.4.0: безопасный userdata `.value` accessor с uint32 bounds, evidence v4, per-field provenance и unsupported list. Константы KFC не подставляются в runtime evidence.
- Исследован `create_resource`: EML сразу добавляет composite GUID/type/part в AppState, а writer сериализует dirty resource после выполнения модов. `GuidRegistryResource` в этом механизме не участвует; неподтверждённая conditional registry mutation удалена. Добавлен read-only `get_resource` lookup по GUID/type без entity с identity/count/fingerprint diagnostics.
- Добавлен evaluator v4 с независимыми A/H/R/V/B/C, совместимостью v3 без синтеза H/R и безусловным `spawn_ready=false`. Observer читает v4 с fallback на v3, остаётся read-only и укладывается в лимит ответа.
- Созданы документы HashKey32/registration/evidence/test/runtime. Runtime report: `NOT_EXECUTED`. Подготовлен только план будущего rollback/reinstall; rollback, установка 0.4.0 и игра не выполнялись.
- Повторная read-only проверка текущей 0.3.0 установки: игра/server закрыты; backup 24/24, install 9/9, DAT baseline 55/55, unknown changes 0, KFC `.bak` совпадает baseline, LOCAL changed 6 и added/removed 0; rollback ready, не выполнен.
- Проверки: Python **298 run / 297 PASS / 1 skipped**; Stage 10.7 targeted **97 PASS**; KFC Inspector **2 PASS**; compileall и `git diff --check` PASS.
- Итог Phase A: **PARTIAL_SUCCESS**. Офлайн механизм обоснован и покрыт тестами, но patch 0.4.0 ещё не установлен и runtime A/H/R/V/B/C не подтверждены. Следующий шаг требует отдельного разрешения на Phase B controlled rollback/reinstall; затем отдельного разрешения на Phase C load-only. Spawn/entity mutations остаются запрещены.

## 2026-11-01 — Stage 10.7 Phase B: controlled rollback и patch 0.4.0 install

- Пользователь отдельно разрешил Phase B при запрете запуска игры, spawn и любых entity/faction/inventory mutations. Перед rollback Enshrouded/server отсутствовали.
- Read-only audit подтвердил старый receipt `complete`, SHA-256 `d8ca5937f03663e7c9e1468890f1126be8e0dcad403bade47384c70d6a1aa15a`, installed hashes 9/9, backup 24/24, исходные DAT 55/55 и атрибутированные нулевые DAT 055–063. KFC `.bak` совпал baseline; неизвестных изменений нет.
- LOCAL набор содержит 22 файла. От исторического pre-run baseline отличаются шесть ожидаемых файлов: `character0.ksd`, `world0.ksd` и по две backup-копии. Они не восстанавливались; их hashes до/после Phase B совпали.
- Штатный rollback удалил ровно 9 receipt paths. Восстановлены только KFC/resources из verified backup; удалены атрибутированные `.bak`, DAT 055–063 и EML runtime directories `.cache/export/logs`. Clean verification: KFC/resources baseline, DAT 000–054, old install paths absent, unknown changes 0.
- Создан новый backup `stage10-7-pre-eml-20261101`: 24 файла, 224 564 012 bytes, 24/24 verified; manifest SHA-256 `7ac4df3609d2609673345d029844dcf8d9181ba768762aa6eb6b62752cb9b651`.
- Установлены ровно 9 файлов patch 0.4.0/evidence v4/read-only observer. Новый receipt `complete`, SHA-256 `3280870774f3b0283bad0cb6e3063e03ca57f42de8de876578fdf90a269bf2e6`; hashes 9/9, semantic version/token/placeholder checks PASS. Публично сохранён только SHA-256 run token `53d2a97472f31e0f3501b584d199c826e1ef86e2b42f4c0b3f63f8af921b871f`.
- Независимая post-install verification: backup files и current sources 24/24, DAT 55, pre-runtime `.cache/export/logs/.bak` отсутствуют, rollback dry-run 9/9, LOCAL unchanged, процессы закрыты.
- Полный Python suite: **301 run / 300 PASS / 1 skipped**; compileall и `git diff --check` PASS.
- Статус: **READY_FOR_PHASE_C_REVIEW**. Phase C не разрешена и не выполнялась; игра не запускалась, evidence v4 runtime ещё отсутствует, A/H/R/V/B/C не оценивались, `spawn_ready=false`.

## 2026-11-01 — Stage 10.7 Phase C preflight

- Пользователь разрешил контролируемый load-only тест с исключительно ручным запуском Enshrouded и запретом spawn/entity/faction/inventory mutations и rollback.
- Read-only preflight выполнен при закрытых игре/server: receipt `complete`, SHA-256 `3280870774f3b0283bad0cb6e3063e03ca57f42de8de876578fdf90a269bf2e6`; installed hashes 9/9; verified backup и его current sources 24/24; DAT 000–054 — 55 файлов; LOCAL baseline — 22 файла; rollback dry-run 9/9.
- Patch 0.4.0, evidence v4 path, observer и общий run token согласованы. Stale evidence, `.cache`, `export`, `logs`, KFC `.bak`, bridge descriptor, install temporary и посторонние EML-моды отсутствуют; conflicts 0.
- Сохранён ignored preflight snapshot с SHA-256 KFC/DAT/LOCAL/install files и log offsets для post-run comparison. Run token не публикуется; его SHA-256 `53d2a97472f31e0f3501b584d199c826e1ef86e2b42f4c0b3f63f8af921b871f`.
- Статус: **READY_FOR_MANUAL_START**. Codex игру не запускал. Следующее действие пользователя: вручную запустить Enshrouded и загрузить только LOCAL `Body Test` slot 1 / `AI Body Test` slot 1, затем сообщить `загрузился`. `spawn_ready=false`.

## 2026-11-01 — Stage 10.7 Phase C: load-only runtime

- Пользователь вручную запустил Enshrouded, загрузил LOCAL `Body Test` slot 1 / `AI Body Test` slot 1 и затем закрыл игру. Codex игру не запускал и выполнил только read-only Bridge/observer/evidence диагностику. Spawn, NPC, entity/faction/inventory mutations и rollback не выполнялись.
- Bridge подтвердил EMF 0.3.2, API 20, protocol 1, build 1273043 и правильный LOCAL-контекст. Observer `status`, `inspect`, `compare` вернул 3/3 полных согласованных ответа; protocol/JSON/token errors отсутствуют, safety flags PASS.
- EML patch 0.4.0 создал evidence v4, сообщил `AIC_EML_TEMPLATE_V4_READY` и `Applied 1 patches`; writer finalized. Export-directory warning восстановился через default path и не помешал созданию export/evidence; serialization/fatal errors отсутствуют.
- Девять HashKey32 source/clone имеют `CONFIRMED`, точные UInt32 совпадают, provenance получен из EML reflection, unsupported list пуст. Template GUID, source GUID, 81 компонентов, component fingerprint `412d61b0`, lookup fingerprint `a7f38d80`, animation graph и visual dependency closure подтверждены. Read-only lookup через EML AssetManager вернул ожидаемую identity.
- Итог evaluator: **LOAD_ONLY_SUCCESS**, A/H/R/V/B/C = PASS, errors/unknowns отсутствуют. `RUNTIME_RENDER_CONFIRMED=UNKNOWN`: entity не создавалась, поэтому экранная модель/материалы/skeleton/animation и lifecycle ещё не проверены. `spawn_ready=false`.
- Post-run при закрытых игре/server: backup 24/24; installed 9/9; исходные DAT 55/55; только ожидаемые пустые DAT 055–063; KFC `.bak` совпадает baseline; resources baseline сохранён; LOCAL 22 файла, changed 7, added/removed 0; unknown changes 0. Rollback ready=true, executed=false.
- Полный Python suite после испытания: **301 run / 300 PASS / 1 skipped**.
- `compileall` и `git diff --check`: PASS.
- Созданы подробный `docs/STAGE10_7_PHASE_C_REPORT.md` и обновлён runtime report. Следующий возможный этап требует отдельного ТЗ и отдельного разрешения на ограниченный spawn-тест; текущий результат такого разрешения не даёт.

## 2026-11-01 — публикация Stage 10.7 Phase C

- Runtime-отчёт, итог `LOAD_ONLY_SUCCESS`, post-run integrity и результаты проверок опубликованы в `origin/master` коммитом `6c03b4b` (`Record Stage 10.7 load-only success`). Runtime evidence, приватный run token, игровые ресурсы и LOCAL-сохранения в Git не добавлялись.

## 2026-11-01 — Stage 10.8 Phase A: safe humanoid spawn preparation

- Прочитано полное ТЗ; выполнены только разрешённые research/offline implementation действия. Игра/server не запускались; моды не устанавливались; KFC/resources, DAT/KSD и LOCAL saves не изменялись; spawn/despawn/rollback не выполнялись.
- Исследован закреплённый EMF commit `08d600155fcadc8e45cc9c6f3932a67c717345be`. Подтверждены `emf.spawn(world,guid,x,y,z)` → uint32 EntityId/0 и `emf.destroy(world,id)` → принятие native вызова; orientation spawn фиксирована identity quaternion. Custom GUID синтаксически принимается, но spawnability нашего EML resource не доказана.
- Установлены блокеры: public Lua не имеет pre-spawn ground/geometry/navmesh query; EntityId переиспользуется и native instance identity/ownership marker отсутствует; clone является villager с `ForceSave`, поэтому persistence/unique lifecycle неизвестны. `destroy=true` не доказывает исчезновение.
- Реализован `companion/safe_spawn.py`: конечный автомат, fail-closed game/template/entity/position/persistence gates, запрет retry/reconnect/reload/duplicate, mock-only emergency stop, evidence v5 validator и publication redaction. Phase A не имеет runtime effect path и всегда `spawn_ready=false`.
- Добавлен выключенный `experimental/emf_safe_spawn` с отдельным namespace. В нём нет spawn/destroy/faction/inventory/save/event/tick/autoload вызовов; mutation-команды возвращают `phase_a_mutation_prohibited`.
- Созданы шесть документов Stage 10.8: API research, safety/evidence contracts, test/install plans и runtime results `NOT_EXECUTED`.
- Targeted Stage 10.8 suite: **54 PASS**, включая все 50 обязательных сценариев ТЗ и Lua syntax. Полный Python suite: **355 run / 354 PASS / 1 skipped**; skip — прежняя Windows directory-symlink privilege проверка.
- `compileall`, Lua syntax и `git diff --check`: PASS. Аудит новых tracked-кандидатов не нашёл бинарников, saves, runtime dumps, приватного Stage 10.7 token или ключей/паролей.
- Read-only локальная сверка: Enshrouded/server закрыты; фактические SHA-256 совпали с Stage 10.7 для `dbghelp.dll`, `dinput8.dll`, patch 0.4.0 Lua и observer. Реальный EMF loader находится в `dinput8.dll`; предположенный путь `emf/emf.dll` отсутствует и не используется.
- Текущий verdict: **BLOCKED_FOR_SPAWN**. Phase B небезопасна до закрытия identity/position/persistence blockers. `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.

## 2026-11-01 — публикация Stage 10.8 Phase A

- Research, fail-closed controller/scaffold, evidence v5, 54 новых теста и документация опубликованы в `origin/master` коммитом `ed467f1` (`Prepare safe humanoid spawn gates`). Runtime artifacts, игровые файлы, saves и приватные токены не публиковались.

## 2026-11-01 — Stage 10.9 Phase A: spawn safety research и lifecycle engineering

- Прочитано полное ТЗ и выполнена только разрешённая offline Phase A. Игра/server не запускались; моды не устанавливались; игровые файлы, KFC/DAT/KSD и LOCAL saves не читались и не изменялись; spawn, destroy и rollback не выполнялись.
- Исследован закреплённый EMF commit `08d600155fcadc8e45cc9c6f3932a67c717345be`. `EntityId` подтверждён как один `uint32`; доступный entity generation, stable instance GUID и ownership metadata не найдены. Lua callback generation и EntityGrid query generation не являются entity generation.
- Подтверждён public native `spawn_ex`: до 15 существующих компонентов добавляются в один spawn slice. API не регистрирует безопасный custom ownership component, поэтому atomic instance marker не получен. Sidecar по EntityId не решает reuse.
- Ground search найден внутри mutation-based teleport: он работает только для существующей entity и возвращается к raw target при отсутствии walkable cell. Стабильные read-only ABI surface normal/capsule clearance/navmesh/danger query не подтверждены; `POSITION=UNKNOWN`.
- Уточнён persistence: runtime research EMF показал, что добавленный `ForceSave` не сохраняет произвольный spawned object, но villagers — отдельное исключение с `ActiveNpcState`, `ActiveNpcStateSaved`, `unique_npc_init/spawns`. Lifecycle custom EML villager остаётся `UNKNOWN`.
- В `companion/safe_spawn.py` добавлены `OwnedEntityIdentity` (`CONFIRMED/AMBIGUOUS/STALE/REUSED/LOST`), identity classifier без выдуманного generation, position validator `VALID/INVALID/UNKNOWN`, persistence classification, atomic-destroy authorization/postcondition и восемь независимых gates с provenance/evidence/confidence/session. Phase A всегда сообщает `spawn_ready=false`.
- Спроектированы два template variant без назначения GUID/npcId и без изменения patch 0.4.0: временный visual test и будущий permanent companion. Подготовлен design-only native extension ABI с fail-closed error codes; DLL/hooks/memory writes не реализовывались.
- Созданы девять документов Stage 10.9 с исследованиями identity/position/persistence/faction/destroy, extension design, variants, gates/recovery, test plan и runtime `NOT_EXECUTED`. README и TEST_RESULTS обновлены.
- Targeted Stage 10.9: **54 PASS**. Полный suite: **409 run / 408 PASS / 1 skipped**; skip — прежняя Windows directory-symlink privilege проверка. `compileall`, Lua syntax 12/12 и `git diff --check`: PASS.
- Итог: **NATIVE_EXTENSION_REQUIRED / BLOCKED_FOR_SPAWN**. Существующий EMF не закрывает одновременно identity, pre-spawn position и custom villager lifecycle. `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
- Следующий шаг: отдельный этап реализации и офлайн-аудита минимального C++ EMF extension только после нахождения подтверждённого identity primitive и read-only geometry ABI. Установка и runtime требуют новых отдельных разрешений.

## 2026-11-01 — публикация Stage 10.9 Phase A

- Код fail-closed gates/identity/position/persistence/destroy, 54 новых теста и девять документов исследования опубликованы в `origin/master` коммитом `4c47045` (`Engineer Stage 10.9 spawn safety`). Бинарники, игровые файлы, saves, runtime dumps и приватные токены не публиковались.

## 2026-11-18 — Stage 10.10 Phase A: game update compatibility audit

- Прочитаны ТЗ, правила и прежние материалы. Начальный HEAD `1b9ecbff01509e89ba7a7497efdb0f0a2dbb2681`, master, working tree чистый. Выполнялась только offline Phase A; Stage 11.0 не начат.
- EXE reflection/SHA и Steam manifest подтвердили **1.0.1.2 / build1287369**, Steam build26430625, depot1203621 manifest7226436020230696061. EXE35 476 040 bytes, SHA `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77`. Проверены официальные updates1283531→1285601→1287369; последнее найденное обновление — 4 ноября. Steam update/verify не запускались.
- Полный read-only inventory:249 game files,23 LOCAL files. Старый receipt9/9 совпал; старые EMF0.3.2/EML0.2.0/patch0.4.0/observer остались. Сохранённый лог от6 ноября показывает EMF idle и38/50 signatures; это не текущий игровой тест.
- KFC/resources/.bak отличаются от Stage10.7,25 из55 исходных DAT изменились,30 совпали; DAT055–063 по-прежнему пустые. Их номера не считаются зарезервированными за EML. База содержит custom GUID, поэтому clean baseline не подтверждён. Публичный inventory:1 UPDATED_BY_GAME,19 PREVIOUS_MOD_ARTIFACT,28 MODIFIED_UNKNOWN,30 UNCHANGED,171 NEW-to-inventory,0 MISSING.
- Заново проверены все5 старых backups:105/105,144/144,24/24,24/24,20/20 —317 файлов. Manifest/receipt Stage10.7 совпали с прежними hashes. Старые manifests не переписаны; восстановление старых game resources поверх нового build запрещено. LOCAL default22 файла совпали с Stage10.7 post-state; совместимость saves с новой игрой не заявляется.
- Последний EMF stable **0.6.18**, commit `fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`, core API46, Lua host1.39.0. Официальный manual-архив скачан только в ignored project runtime; SHA `12bbcae2e52386bcd7f1747701bb6d1ec8a64fab061e6e33ce994b6ee29c926b` совпал с GitHub asset digest. Четыре нужные DLL —x64, NotSigned; binary/source reproducibility и runtime не подтверждены. DLL/EXE/installer из пакета не запускались.
- EML upstream остаётся **0.2.0**, commit `16708594d686b030d909f2d835b199d879ea9ad8`; обозначение EML0.3.2 в ТЗ неточно. Новый EMF содержит patched EML `emf_content.dll` и shadow content loader, который выключает export и уступает standalone dbghelp. Наш evidence export требует отдельной адаптации/выбора content owner.
- Из установленного EXE извлечены12658 types; generated comparison:1283 identical по доступным полям,4 layout changes,2 additions. Старые alignment/full resource schemas не везде доступны и остаются UNKNOWN. Публикуются metadata/diff, не raw EXE dumps.
- Повторно прочитаны64 KFC resources:58 совпали,6 изменились. Hunter/blacksmith/clone теперь82 components, добавлен GrassEffector; source movement/AI values изменились. Observed component fingerprint `5253f478`. Все9 HashKey32 source/clone, graph, selected preset18 references,35 models и hierarchy102 joints сохранены. Source/clone отличаются только name/npcId/faction; чистота source/collision-free clean base не доказана. Runtime render UNKNOWN.
- Реальные install/rollback helpers получили EXE/build/baseline/manifest/target guards. Старый broad directory cleanup выведен из использования. Legacy receipt не разрешает удаление; DAT по одному имени не удаляются. Добавлены profiles1273043/1287369 без fallback, evidencev7 и offline readonly capture validator.
- Для будущего patch0.5.0 подготовлена read-only Lua compatibility guard library, без mod.json/регистрации ресурсов. Готового устанавливаемого patch/observer нет: clean baseline, GUID/npcId collision audit и evidence channel блокируют выпуск. Историческая0.4.0 не изменена.
- Stage10.9 пересмотрен: upstream теперь предоставляет ground_at/path_find/villager_move; собственные дубликаты этих функций не нужны. Native instance identity/ownership/atomic destroy, full clearance и custom villager persistence остаются нерешёнными. Safety gates не ослаблены.
- Python: **525 discovered/testsRun,524 executed/PASS,0 failed,1 skipped**; новые116 PASS, regression408 PASS/1skip. Skip — прежний Windows directory-symlink WinError1314. Rust Inspector2 PASS; upstream C++ ground/search/path30 cases/730 assertions PASS; Lua syntax13/13, compileall и diff check PASS. Это fixtures/fake-engine tests, не runtime acceptance.
- Полный before/after: **249/249 game +23/23 LOCAL неизменны**, added/removed/changed=0 по paths/SHA/size/mtime. Tasklist helper на финале не смог проверить процессы в ограниченной среде; независимый Get-Process успешно подтвердил отсутствие game/server до/после final inventory. Ошибка не трактовалась как разрешение изменений.
- Созданы15 документов Stage10.10, публичные sanitized audit metadata, profiles/evidence; обновлены README и TEST_RESULTS. Raw game data, saves, upstream binaries, private tokens остаются ignored.
- Verdict **BLOCKED_BY_GAME_INTEGRITY**, дополнительные EML/evidence и clean-resource blockers. `installation_ready=false`, `runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`. Игра/server не запускались; install/cleanup/rollback/restore/spawn/entity mutations не выполнялись.
- Следующий шаг: опубликовать этот offline audit в origin/master и остановиться. Phase B требует отдельного согласования clean-baseline/cleanup/content-owner плана после закрытия блокеров; Phase C не готова.

## 2026-11-18 — публикация Stage 10.10 Phase A

- Код, 116 новых тестов, 15 документов, profiles/evidence v7 и sanitized metadata опубликованы в `origin/master` коммитом `cb164a8` (`Audit build 1287369 compatibility and block cross-build rollback`). Push подтверждён; HEAD и origin/master совпали, working tree после публикации был чистым.
- Проверены именно staged Git blobs profiles: их LF-нормализация не нарушает закреплённые SHA-256 после клонирования. Staged evidence v7 прошла validator. В коммит не вошли DLL/EXE, archives, raw game dumps, saves и private token.
- Итог сохраняется: **BLOCKED_BY_GAME_INTEGRITY**, installation/spawn ready=false, runtime NOT_EXECUTED. Дальнейшие Phase B/C/Stage11.0 не выполняются; требуется отдельный review clean baseline и content/evidence integration.

## 2026-11-18 — Stage10.10.1 Phase A: recovery и mod migration preparation

- Открытие папки проекта в VS Code работу не прервало. Прочитаны AGENTS/PROGRESS и полное ТЗ; выполнена только Phase A. Начальный HEAD7d45464, working tree был чистым.
- Fresh read-only before/after:249 game +23 LOCAL files; zero added/removed/changed по paths/SHA/size/mtime, также без отличий от Stage10.10. Process checks game/server=0. EXE/build1287369 и Steam build26430625/depot manifest7226436020230696061 повторно подтверждены.
- Создан machine-readable cleanup manifest272 записей:81 QUARANTINE exact-hash attributed,57 STEAM_REPAIR,51 MANUAL_REVIEW,83 KEEP. Повторно проверены receipt9 и old manual archive entries; DAT055–063 не атрибутируются по пустому SHA/номеру. Unknown body.lua/config/cache/log/export/bak/vendor files не удаляются.
- Подготовлена Backup1 strategy419971833 bytes (~400.52MiB), карантин29504495 bytes; полный mixed backup потребовал бы51924042489 bytes. Тела DAT в рекомендованный ограниченный backup не входят: полного возврата mixed state после Verify не обещаем. Backup2 создаётся после clean audit; фактические новые backups не создавались.
- Добавлены recovery library/CLI: build/Steam/receipt/hash/size/inventory guards, default dry-run, explicit execution authorization, verified copies и per-file quarantine journal, path/reparse/hardlink/overlap refusal. Настоящий CLI dry-run: DRY_RUN_VALID, unresolved51, cleanup_executed=false. Сам backup/quarantine выполнялся лишь в test fixtures.
- GitHub API заново подтвердил EMFv0.6.18 и EMLv0.2.0. По pinned EMF source исследованы Companion1.7.0, Beastmaster1.18.1, VillagerJobs1.5.3 и MIT/GPL boundaries. Companion default Vukah и sidecar gear не равны humanoid/rendered equipment. Логический owner/account/npcId не решает instance reuse/atomic destroy.
- Рекомендован integrated content как кандидат: private shadow KFC/resources, controlled DAT hardlinks/writer; standalone одновременно запрещён. Подтверждён print→content.log channel при export=false; нужны отдельные writer/state/unload/readback и свежая session/world binding. Source mechanism не выдан за runtime success.
- Подготовлены offline evidence emitter/parser v8 и readonly observer library status/inspect/compare; mutations запрещены. Без mod.json/bootstrap/live capture и доверенного clean evidence baseline. Historical patch0.4/BodyClient не менялись;0.5 остаётся PATCH_PREPARATION_ONLY. Фиксированные82 components не объявлены новым clean контрактом.
- Созданы14 документов: recovery/manifest/backup/Steam/baseline/owner/evidence, три mod research, reuse matrix, native review, roadmap, PhaseA report с26 ответами. README и TEST_RESULTS обновлены. Ground/path/villager primitives повторно разрабатывать не предлагается; minimal native identity/ownership gap остаётся.
- Полный Python:586 testsRun,585 PASS,1 прежний skipped,0 failures;61 новый PASS. Новый Windows junction/root escape и hardlink tests PASS. Lua syntax15/15, compileall PASS. Rust/C++ не менялись и повторно не запускались. Runtime game/Bridge не проверялись.
- Вердикты BLOCKED_BY_UNKNOWN_ARTIFACTS / BLOCKED_BY_GAME_BASELINE, PARTIAL_UPSTREAM_REUSE. cleanup_executed=false, clean_baseline_confirmed=false, installation_ready=false, runtime_status=NOT_EXECUTED, RUNTIME_RENDER_CONFIRMED=UNKNOWN, spawn_ready=false.
- Игра/server/Steam Verify не запускались; game/LOCAL/receipt не изменялись; install/rollback/restore/spawn не выполнялись. Следующий шаг — публикация Phase A и остановка; отдельное разрешение нужно для Phase B backup+ограниченного карантина81, либо сначала дополнительная атрибуция51 неизвестной записи. Полная очистка/установка не готовы.

## 2026-11-18 — публикация Stage10.10.1 Phase A

- Исходники,61 новый тест,14 документов и sanitized recovery/integrity metadata опубликованы в origin/master: `63732f93bea181087511a9d06e0c137f0ffae61f` (`Prepare Stage 10.10.1 recovery and mod migration`). Push подтверждён; HEAD и origin/master совпали, working tree был чистым.
- Перед публикацией проверены26 staged files: diff whitespace, локальные ссылки, manifest counts/flags, отсутствие приватного run token и Steam LastOwner; бинарники/archives/game/save contents не вошли в коммит. Окончательный suite после всех backup changes:585 PASS/1skip.
- Recovery backup теперь содержит отдельный plan.json со всеми DAT hashes, приватный receipt и manifest с точными backup paths; это реализация для будущей Phase B, реальные backups не создавались. Обновление PROGRESS фиксирует состоявшуюся публикацию, не разрешение очистки.
- Работа остановлена перед Phase B. Full cleanup остаётся BLOCKED_BY_UNKNOWN_ARTIFACTS; установка/игровой тест/spawn не готовы. Следующее согласование — ограниченный backup419971833 bytes и карантин только81 атрибутированного файла, с сохранением всех51 MANUAL_REVIEW на месте; либо дальнейшая атрибуция до этих действий.

## 2026-11-18 — Stage10.10.1 limited Phase B: verified backup

- Получено отдельное разрешение пользователя: backup около420MB, карантин только81 reviewed файла, остальные51 без изменений; без Steam Verify/игры/server/новых модов/старого rollback. Неполный DAT backup принят; integrated content принят как будущая архитектура с integrity gates. Phase C не разрешена.
- Исходный HEAD21d7860, working tree был чистым. Reviewed manifest совпал побайтно с commit; SHA256 `2d699685c12cb39edc69e924c6a887b4f22dacb218f10ab271713610e3097e4d`. Fresh inventory249 game/23 LOCAL полностью совпал с Phase A по SHA/size/mtime. Game/server=0; Steam manifest StateFlags4, download/stage byte counters завершены.
- Штатным backup CLI создан `C:\Enshrouded-ai-companion\runtime\backups\stage10-10-1-phase-b-20261118T1035Z`. Проверены208 payload files + приватный receipt:209/209 SHA/size; отдельный verify-backup тоже BACKUP_VERIFIED. Вместе с plan.json/manifest.json:211 файлов,420406619 bytes; payload419971833 bytes. Все64 DAT представлены hashes в plan, их тела не копировались. Полный mixed-state restore не обещается.
- Targeted recovery/migration tests заново:61 PASS. Ресурсы игры и LOCAL только читались, не изменялись. Следующий разрешённый шаг — штатный карантин81 после повторного preflight, затем fresh post-inventory.

## 2026-11-18 — Stage10.10.1 limited Phase B: карантин выполнен

- Штатный quarantine CLI завершился успешно: `quarantined=81`. Destination: `C:\Enshrouded-ai-companion\runtime\quarantine\stage10-10-1-phase-b-20261118T1035Z`; journal содержит81 завершённую запись QUARANTINED после81 COPIED_VERIFIED_SOURCE_PRESENT.
- Перемещались только строки QUARANTINE reviewed manifest, через проверенную копию и per-file unlink. Директории целиком, неизвестные файлы, DAT/KFC/resources и LOCAL не удалялись. Содержимое карантина сохраняется. Старый rollback не применялся; новых модов нет.
- Следующий шаг — полный post-inventory, независимая проверка всех81 копий/журнала и сохранности остальных файлов. Полная чистота baseline пока не заявляется.

## 2026-11-18 — Stage10.10.1 limited Phase B: post-audit и остаточные файлы

- Fresh post-inventory:249→168 game files; исчезли ровно81 reviewed пути, added=0, changed=0. Все168 оставшихся файлов совпали по SHA/size/mtime. Все51 MANUAL_REVIEW,64 DAT,23 LOCAL без изменений; EXE/KFC/resources/.bak сохранены. Game/server после операции=0.
- Post-audit повторно проверил209 backup payload files и81 карантинную копию по SHA/size. Журнал162 записи полностью совпал с планом; лишних payload files нет. Backup manifest SHA `67a542553c82328bcdd589a1f4067c034bf0315fa8e375dd5a89b341c177333b`, quarantine journal SHA `27a3a7b79a590e692c14584d1106a3a4f20112e2f26cad005a32abb1e52237d9`. Карантин не очищался, historical receipt неизменен.
- По всем51 остаточным файлам создан sanitized review. KFC64 containers/.bak55 при одном build: integrated choose_base выбрал бы .bak; чистота обоих не доказана. Пустые DAT055–063 остаются provenance blocker. Их содержимое/индексы не изменялись; повторное декодирование64 resources не выполнялось, прежний clone finding относится к hash-неизменившейся базе.
- body.lua byte-for-byte совпал с историческим026cd8a; он всё равно оставлен согласно разрешённому scope.23 configs включают aic_body/Lua enabled1 и debug bridge1/verbose1;4 cache-файла, legacy catalog69 строк и exportv4 нельзя слепо наследовать. Без loaders/main/mod.json старый adapter не запускается.
- У NVIDIA Aftermath, DLSS и Valve steam_api64 Authenticode Valid; это vendor evidence, не доказательство Steam depot hashes. Settings JSON и7 исторических diagnostic files не дают основания для дополнительного удаления. Все51 сохранили original action и содержимое.
- Добавлены read-only post-audit helper,11 тестов, подробный Phase B report и residual review; README/TEST_RESULTS обновлены. Полный Python:597 testsRun,596 PASS,1 прежний skip,0 failures; compileall/diff checks PASS. Lua/Rust/C++ не менялись и повторно не запускались.
- Verdict LIMITED_PHASE_B_COMPLETED. cleanup_executed=true только для81; clean_baseline_confirmed=false, installation_ready=false, phase_c_executed=false, runtime NOT_EXECUTED, render UNKNOWN, spawn_ready=false. Integrated content принят пользователем условно на дальнейший этап; новых модов нет.
- Следующий шаг — публикация отчёта/metadata/helper/tests и остановка. Phase C требует отдельного согласования; Steam Verify/игра/server/install/старый rollback/restore не выполнялись. Backup/quarantine остаются в ignored runtime и не публикуются.

## 2026-11-18 — публикация limited Phase B

- Результаты Phase B, read-only helper/11 тестов, отчёт и пофайловый разбор51 остатков опубликованы в origin/master: `f61441b5a4a359b92aedbce4fa4c2838faf78e51` (`Complete limited Phase B backup quarantine and residual audit`). Push подтверждён, HEAD и origin/master совпали.
- Проверены10 staged files: diff/links/scope flags и отсутствие private run token/Steam LastOwner, бинарников и game/save payload. Backup209 payload files и карантин81 остаются только локально; игровые файлы больше не изменялись после завершения разрешённого карантина.
- Старый install receipt сохранён как исторический документ: после снятия файлов он не является доказательством текущей установки и не разрешает старый rollback. Текущее состояние описано новым operation.json и журналом карантина.
- Остановлено перед Phase C. Итог LIMITED_PHASE_B_COMPLETED; чистый baseline, новая установка, shadow integrity и runtime пока не подтверждены; spawn_ready=false. Никаких следующих действий без отдельного согласования Phase C не выполняется.

## 2026-11-18 — Phase C/D: повторный аудит перед согласованием

- Прочитано новое ТЗ Phase C/D. Разрешены read-only аудит и офлайн-разработка; дополнительный карантин требует точного списка и подтверждения, Steam Verify выполняет пользователь. Установка не разрешена.
- Свежий полный inventory:168/168 игровых и23/23 LOCAL совпали с post-Phase-B по paths/SHA/size/mtime. Процессы игры/server отсутствуют. EXE/profile1287369 и Steam build26430625/depot7226436020230696061 совпали; это не доказательство чистой resource database.
- Backup заново проверен209/209; карантин81/81 и журнал162 записей совпали с pinned manifest/hash. Новые резервные копии не создавались. Старый receipt не используется для подтверждения текущей установки.
- Создан read-only helper и дополнительный proposal:30 mod/config/cache/catalog/evidence файлов, отдельное согласование удержания KFC.bak,20 файлов оставить. Proposal не поддерживает выполнение; game/DAT/LOCAL не изменены.
- KFC64/.bak55 остаются смешанной базой. Clean acceptance, post-Steam audit и clean backup ещё не выполнены. Следующий шаг — тесты и независимая разработка shadow validator, затем публикация конкретного списка для согласования. spawn_ready=false.

## 2026-11-18 — Phase C/D: независимая офлайн-разработка и итоговая проверка

- Реализован read-only shadow filesystem validator: exact client path/allowlist, no reparse, volume/file identity, SHA/size/mtime, private indexes и разрешённые base hardlinks, дополнительное чтение originals.14 fixture tests PASS, включая реальную junction, запись через synthetic DAT link и unlink-before-write. Writer/redirection/resource semantics остаются UNKNOWN; filesystem PASS не runtime PASS.
- Подготовлен component subset официального EMF0.6.18 под `dist/stage10_10_1_integrated_components_20261118_r2`:8 game candidates+12 notices. Archive digest повторно совпал с актуальным GitHub API;4 DLL x64/PE32+, Authenticode NotSigned. Ничего не запускалось/не устанавливалось. Первый staging candidate заменён r2 после исправления INI-секции `[lua]`; в review указан только r2.
- Core/Bridge/content configs подготовлены вне игры; gameplay mods/legacy Body/installer не включены. Profile1287369 фиксирует выбор integrated owner, но clean contract/patch остаются blocked. Исторические profile1273043/patch0.4 не менялись. Полный migration package, observer/bootstrap, evidencev8 capture, Bridge migration, exact install receipt/rollback ещё не готовы.
- Полный Python619 testsRun:618 PASS,1 прежний skip,0 failures. Новые22 tests (residual6/staging2/shadow14). Lua syntax15/15, compileall PASS. Rust/C++ не менялись и не перезапускались. Логи fake patch из tests не являются свидетельством запуска игры.
- Итоговый полный inventory совпал с начальным и Phase B:168/168 game,64 DAT,51 residue,23/23 LOCAL без изменений. New backups0 bytes. Все31 proposed targets уже покрыты повторно проверенным backup; никакие дополнительные файлы не перемещались.
- Подготовлены Phase C report с post-Steam/clean статусами, Phase D partial report с21 ответом, exact approval list, shadow contract и future load-only plan. Нет пустых отчётов, изображающих выполненный Steam repair или clean acceptance.
- Список для согласования:30 mod/config/cache/catalog/evidence файлов12660171 bytes и отдельно KFC.bak9396224 bytes; всего31/22056395 bytes. Proposal SHA `6e7f462af6ee5d15f0fed6d4eb9b14b06c25f0603dfdcfca2f8456ca5eda6445`. Остальные20 из51 остаются; DAT/KFC/resources/LOCAL не затрагиваются. `.bak` не объявляется mod-owned/vanilla; старый recovery CLI запрещает его перенос, обходить защиту нельзя.
- Verdict CLEAN_BASELINE_BLOCKED / MIGRATION_PACKAGE_PARTIAL. Следующий шаг — публикация и отдельное согласование31-file scope, затем контролируемая очистка и ручной Steam Verify. Phase E/F не готовы и не разрешены. installation_authorized=false, installation_executed=false, runtime_status=NOT_EXECUTED, RUNTIME_RENDER_CONFIRMED=UNKNOWN, spawn_ready=false.

## 2026-11-18 — публикация pre-Steam Phase C/D

- Опубликован commit `a73a50dd40734f90b800be58fe4a12b70e9f2c09` (`Prepare Phase C residual review and integrated shadow checks`); push origin/master подтверждён, HEAD совпал с origin/master, working tree был чистым.
- После последних code/profile изменений полный suite повторён:619 testsRun/618 PASS/1skip; compileall и Lua syntax15/15 PASS. Проверены локальные Markdown links, LF/profile SHA и git diff.26 staged текстовых файлов прошли проверку на private run token/Steam account metadata; бинарников/resources/save payload в коммите нет.
- Дополнительное перемещение30 mod artifacts и отдельного KFC.bak пока не разрешено и не выполнялось. Steam Verify ещё не запускался. Подготовлены точные hashes/происхождение/restore policy; все31 файла покрыты existing verified backup. Остановка на контрольной точке пунктов4/7/9 нового ТЗ; ожидание подтверждения этого списка. Установка Phase E, игра/server и NPC по-прежнему не разрешены.

## 2026-11-18 — Phase C: получено разрешение на31 файл, подготовлен исполнитель

- Пользователь отдельно разрешил30 mod artifacts из pinned residual-proposal и удержание enshrouded.kfc.bak в новом карантине. Остальные20, original KFC/resources/EXE/DAT и LOCAL запрещено изменять; backup/старый карантин сохраняются. Steam Verify выполняет пользователь после сигнала готовности.
- Proposal SHA заново совпал с `6e7f462af6ee5d15f0fed6d4eb9b14b06c25f0603dfdcfca2f8456ca5eda6445`; исходный HEAD b608cef, рабочее дерево было чистым. Game/server отсутствуют.
- Добавлен отдельный Phase C executor с двумя явными authorization flags, pinned proposal/commit, build/Steam/process guards, новыми receipt/journal. Сначала копирует и проверяет все31 файла; затем повторно проверяет source/backup/quarantine перед каждым unlink. Старый Phase B запрет KFC.bak не менялся; restore/recursive cleanup/retry отсутствуют.
-12 новых fixture tests PASS: exact31/20 KEEP, отдельное согласие .bak, protected path/hash/build/LOCAL guards, copy/unlink failures, partial journal/no resume, overlap/hardlink refusal. Первоначальный тест повторного вызова выявил порядок отказа; проверка existing destination перенесена перед source validation, затем12/12 PASS. Игровых операций этот тест не выполнял.
- Запущен настоящий dry-run без удаления: backup209/209 и старый карантин81/81 уже повторно проверены; идёт full inventory. Фактическое перемещение пока не выполнено. Следующий шаг — завершить preflight/полный suite, затем выполнить разрешённый scope31.

## 2026-11-18 — Phase C: разрешённый карантин выполнен, идёт post-audit

- Dry-run завершился DRY_RUN_VALID:168 game/23 LOCAL,31 selected,22056395 bytes, identity и pinned inventory совпали. Полный suite631 testsRun/630 PASS/1 прежний skip; compileall/diff check и Lua syntax15/15 PASS.
- После повторного preflight исполнен разрешённый scope. Новый карантин: `runtime/quarantine/stage10-10-1-phase-c-20261118T1122Z`. Журнал содержит31 COPIED_VERIFIED_SOURCE_PRESENT, затем31 QUARANTINED. Все копии были проверены до первого unlink; исходные имена снимались по одному с повторной SHA/process/build проверкой.
- Исполнитель сообщил quarantined=31 и перешёл к full post-inventory. Это ещё не итоговый clean-baseline verdict или разрешение Steam Verify: контроль сохранности137 оставшихся игровых файлов,20 KEEP,64 DAT и23 LOCAL пока выполняется. `.bak` только удержан в карантине, не применялся поверх KFC. Игру/server/установку/spawn не запускали.

## 2026-11-18 — Phase C: post-audit PASS, готовность к ручному Steam Verify

- Исполнитель завершился exit0, READY_FOR_MANUAL_STEAM_VERIFY. Full inventory168→137 game: removed точно31 reviewed пути, added0/changed0.137 remaining,20 KEEP,64 DAT и23 LOCAL идентичны по paths/SHA/size/mtime. EXE/KFC/resources SHA прежние; original resource writes отсутствуют. Новый clean baseline ещё не получен.
- Старый backup209/209 и quarantine81/81 повторно проверены до/после; SHA всех файлов и metadata в этих папках сохранились. Новый карантин31 payload files22056395 bytes; с proposal/authorization/journal/receipt35 files22115563 bytes. Содержимое сохранено, в Git не публикуется.
- Journal SHA `ebacb25843d035858ec563b0d65f54cd61abcebf97fc4120856eda677e7424d8`,62 records. Receipt SHA `2fbd68b5394c03256d7aaa4109b6dae14591e0ff8e9580e692e5e17a890385ad`; независимая проверка копий, receipt bytes и delta PASS. Public cleanup-operation.json содержит hashes/metadata, не game/save contents.
- KFC.bak отсутствует только в исходном пути и сохранён в новом карантине; не объявлен vanilla и не применялся поверх KFC. DAT055–063/остальные20 не переносились. Не выполнялись старый rollback, восстановление saves, запуск игры/server, модов или spawn.
- Создан фактический cleanup report, обновлены README/TEST_RESULTS/Steam Verify инструкция и ссылки из исторического pre-cleanup review. Следующий шаг — пользователь вручную выполняет Steam Verify и сообщает результат, игру не запускает. После сообщения разрешено продолжить post-Steam Phase C/D по прежнему ТЗ без нового согласования read-only аудита; установка по-прежнему отдельно.
- Итог READY_FOR_MANUAL_STEAM_VERIFY; steam_verify=NOT_EXECUTED, clean_baseline_confirmed=false, installation_authorized=false, installation_executed=false, runtime_status=NOT_EXECUTED, RUNTIME_RENDER_CONFIRMED=UNKNOWN, spawn_ready=false. Ограниченный backup без DAT-тел не гарантирует полный возврат mixed state после Steam; новая полная копия не создавалась.

## 2026-11-18 — публикация выполненной Phase C очистки

- Commit `4b58205140497ae48e665a2da5416affe2f26a52` (`Complete approved Phase C residual quarantine and integrity audit`) опубликован в origin/master. HEAD и origin/master совпали, working tree был чистым.
-12 staged text files прошли diff/Markdown links/UTF-8 и проверку отсутствия private run token/Steam account metadata и бинарных/game/save payload. Новый карантин35 файлов и старые backup/quarantine остались только локально.
- Пользователю можно запускать Steam Verify вручную: Библиотека → Enshrouded → Свойства → Установленные файлы → Проверить целостность. Дождаться завершения и сообщить результат; Enshrouded/server не запускать. Ожидание этого сообщения — следующий обязательный checkpoint перед post-Steam Phase C/D. Модификации не устанавливаются и spawn_ready=false сохраняется.

## 2026-11-18 — post-Steam: восстановление завершено, первичный read-only аудит

- Пользователь сообщил о завершении Verify (диалог: один файл будет загружен заново). Повторно прочитаны Steam appmanifest и content_log: repair завершён 14:28:16 MSK, No Error, StateFlags=4, download 4566592/4566592 и stage 9396224/9396224. Build1287369 / Steam26430625 / depot7226436020230696061 прежние. Game/server отсутствуют. Агент Steam/game не запускал.
- Новый full inventory `runtime/stage10_10_1_post_steam/20261118-audit/inventory.json`:137 game/23 LOCAL. Относительно успешного Phase C cleanup изменились ровно KFC и resources; добавлений/удалений нет,135 game и23 LOCAL неизменны. KFC SHA2093a7cc…460bf5; resources стал215052288 bytes, SHA2f54eb9e…9d91a7. EXE и64 DAT неизменны. Сохранённые20 KEEP не изменялись.
- Старый clone GUID отсутствует (lookup count0).64 исходных ресурса повторно декодированы прежним проверенным Inspector, все равны pre-Steam значениям; animation graph дополнительно найден и декодирован. Новый read-only режим Inspector проверил55 containers,101492 content references,91909 resource identities,58 chunks и12269 templates: duplicate IDs0, npcId2939921867 collisions0. Rust3/3 tests и locked/offline release build PASS; Cargo.toml/Cargo.lock прежние, source safety audit PASS.
- Найден plaintext depot cache1203621_7226436020230696061.manifest. Новый ограниченный read-only parser проверяет framing/protobuf/CRC/identity/paths и сравнивает файлы:61/61 size+SHA1 PASS, одновременно вычислены SHA256.12 новых Python fixture tests PASS. Signature section пустой; криптографическая upstream-аутентификация не заявляется. Полный итоговый baseline evaluator и проверка неизменности после чтения ещё предстоят; предварительный статус PARTIAL, не CONFIRMED.
- Ничего в игре/LOCAL/backup/quarantine не записывалось. Новый clean backup и установка ещё не выполнены; Phase D остаётся подготовкой. Следующий шаг: закончить post-Steam evidence/acceptance, затем разрешённые backup и офлайн-миграцию с сохранением installation_authorized=false и spawn_ready=false.

## 2026-11-18 — post-Steam audit завершён; PARTIAL и ограниченное acceptance

- Опубликованы в рабочем дереве новый post-Steam report, metadata audit и source contract. Steam content_log объяснил обе перемены:9 KFC chunks заменены, resources усечён на4096 bytes. Source82 components/FNV5253f478,18 preset references,102 joints и9 typed HashKey32 подтверждены заново; полный scan12269 templates исключил npc2939921867. Сырой game/save/depot content в Git не добавляется.
- Контрольный полный inventory после чтения:137/137 game и23/23 LOCAL совпали с начальным post-Steam inventory. Backup209/209, Phase B quarantine81/81 и Phase C quarantine31/31 проверены заново; ничего не восстанавливалось, не перемещалось и не удалялось. Игра/server закрыты, Steam idle.
- Выявлена и исправлена предпосылка shadow validator:55 containers из KFC нужно отличать от64 DAT-файлов в root. Девять пустых055–063 не входят в depot и не являются base links; сохраняются original single-link/hash/identity/mtime. Одноимённый generated DAT допускается только как private shadow file.2 новых safety fixtures PASS. Реальный writer не запускался.
- Итог evaluator CLEAN_BASELINE_PARTIAL:10 локальных checks PASS, failures0; independent_depot_hashes=false, signature отсутствует. Пользователю предложено ограниченное принятие именно этой базы по разделу12 ТЗ Phase C/D. Согласие пока не получено; `PROPOSED_NOT_GRANTED`. Оно не даст разрешения на установку и не изменит формальный verdict на CONFIRMED.
- Backup рассчитан:27 payload files260563026 bytes (~260.6 MB): EXE/KFC/resources/config+23 LOCAL, без DAT bodies, отдельно от mixed backup. Не создан до baseline acceptance. Полный Phase D candidate пока не готов; новые source evidence и исправленный shadow validator готовы к продолжению. Patch0.4, исторические profiles и установленные игровые файлы не изменены.
- Полный Python suite645 testsRun/644 PASS/1 прежний skip/0 failures (12.323s). Новые depot12 и shadow2 tests PASS. Rust3/3 tests, locked/offline release build и source/dependency guard PASS; новая бинарная сборка SHA81531333…14f075 остаётся только в .tools/target. Compileall, Lua syntax15/15 и diff check PASS. C++ не менялся и повторно не проверялся.
- Следующий шаг: зафиксировать/опубликовать audit и дождаться решения по ограниченному acceptance; при согласии повторить источники/preflight, создать verified backup и завершить offline Phase D по прежнему ТЗ. installation_authorized=false, installation_executed=false, runtime NOT_EXECUTED, render UNKNOWN, spawn_ready=false.

## 2026-11-18 — публикация post-Steam проверки

- Commit `a53621a` (`Audit Steam repair and distinguish base DAT from preserved residues`) успешно отправлен в origin/master; HEAD и remote-tracking ref совпали, рабочее дерево было чистым. Опубликованы16 текстовых файлов с отчётом, hashes/metadata, исходниками и тестами. Private receipt token/Steam account value, бинарники, игровые/save payload, backup и карантины не включены; staged diff/UTF-8/JSON/local links checks PASS.
- Подтверждены завершение ремонта Steam,61/61 depot matches, отсутствие старого clone, неизменность23 LOCAL и сохранность backup/quarantine. Формальный итог PARTIAL из-за неподтверждённой подписи локального depot cache. Вопрос об ограниченном принятии baseline остаётся ожидающим ответа; новый backup260.6 MB только спланирован, установка и игровой тест не выполнялись. Следующий шаг после принятия — backup и завершение офлайн-Phase D, затем отдельное согласование установки. spawn_ready=false.

## 2026-11-18 — ограниченный baseline принят, verified clean backup создан

- Пользователь явно принял CLEAN_BASELINE_PARTIAL и отказался от дополнительной upstream-аутентификации на этом этапе; разрешены backup и полная офлайн-Phase D. Формальный verdict не повышается до CONFIRMED. Установка/game/server/spawn запрещены.
- Fresh preflight подтвердил тот же полный inventory137 game/23 LOCAL, Steam26430625/depot7226436020230696061 idle, игру/server закрыты. Все16 будущих install destinations отсутствуют. Подтверждённые механизмы заново не исследовались.
- Новый отдельный backup `runtime/backups/stage10-10-1-clean-20261118`:27/27 payload SHA256 PASS,260563026 bytes; с baseline/future-targets/manifest —260600882 bytes. Manifest SHA `d671fd038634433b3400682e0b0f7e513a854111b3ca96e123e76b1d1e59250a`. Payload:EXE/KFC/resources/local config+23 LOCAL; DAT-тела не копировались, полный inventory их hashes сохранён.
- Ограниченное acceptance связано с audit SHA8295655c…8de30 и baseline SHAaeb28660…2e58d. Свежие backup receipt/result и16 planned target paths сохранены отдельно от исторических receipts. Backup helper прошёл4 tests: roundtrip/corruption, refusal без acceptance/stale source, partial-copy/no resume, process/unknown-file guards.
- Все старые backup/quarantine tree hashes сохранились. Полный post-backup inventory137 game/23 LOCAL идентичен preflight. Никакой записи в игру/saves не было. Следующий шаг — завершение patch0.5/evidencev8/observer/Bridge/profile/package/rollback dry-run и полный suite. spawn_ready=false.

## 2026-11-18 — офлайн-Phase D завершена, пакет готов к согласованию Phase E

- Создан самостоятельный candidate patch0.5.0 для EMF0.6.18 integrated content/API46/Lua1.39.0/build1287369. Исторический0.4 не менялся. Guard проверяет82 components/девять typed HashKey32,63 dependencies,18 preset reference slots,102 joints,graph/RenderEquipment,enumPlayerAlly11,source/clone identity,GUID/npc collision scan. Все source reflected values и clone components сравниваются; NPC не создаются.
- Готовы полный evidencev8 (40 fields+BEGIN/END), strict parser, observer0.3.0 manifest/bootstrap/config/binding и read-only Python Bridge status/inspect/compare. Runtime EML API не выдуман: после DLL unload Lua сообщает только session/character, а Python сверяет LOCAL/world/build/API/host через Bridge. Fresh nonce/session/profile/plan обязательны. Writer state/fingerprint validator отделён от print/evidence, shadow/readback/redirection и render.
- Обновлён profile1287369 и его pinned index. Новый local package `dist/stage10_10_1_phase_d_20261118`:16 exact game files+12 local licences+plan/binding. Official archive/member hashes повторно проверены; ничего не запускалось. Public manifest не содержит private run token или binary payload. Plan SHA82db6fe28bfff96a6580d7a01cd497ad595baf68fe3098312b95181d27ba9463. Реального install receipt нет до разрешённой установки.
- Финальный preflight:137 game/23 LOCAL неизменны,16 destinations отсутствуют,game/server closed,Steam idle. Backup27/27 и исторический209/209,карантины81/81+31/31 PASS. Исправлен namespace history capture: одинаковое имя папки backup/quarantine B приводило к потере backup entry в словаре. Старый capture сохранён; вместо неверного заявления о его полном покрытии старый backup повторно проверен по pinned manifest/plan/receipt. Будущие capture используют полный относительный путь.
- Новый rollback dry-run проверил16/16 installed fixture files и current-build receipt in memory; ничего не удалено. Реальный runtime shadow пока отсутствует; его появление требует свежей attribution/link audit и отдельного cleanup manifest. Original KFC/DAT/LOCAL автоматически не восстанавливаются, старый rollback не используется.
- Полный Python suite685 testsRun/684 PASS/1 прежний skip/0 failures,12.448s. Новыеbackup4+integrated36 PASS; compileall PASS; Lua syntax19/19 PASS. Decoded-source Lua fixture с82 реальными ранее считанными components/63deps/18refs/102joints PASS; это fake resource API, не EML runtime. Native не менялся и повторно не запускался. Подробности TEST_RESULTS.
- Сохранён предыдущий Phase D preparation report; новый отчёт содержит exact paths/hashes,21 ответ ТЗ, ограничения и порядок Phase E/F. Verdict MIGRATION_PACKAGE_READY/READY_FOR_PHASE_E_APPROVAL при принятом PARTIAL. Установка не разрешена/не выполнена, runtime NOT_EXECUTED/render UNKNOWN/spawn_ready=false. Следующий шаг — diff/staged safety checks, commit/push, затем отдельное разрешение пользователя на установку16 файлов без запуска игры.

## 2026-11-18 — публикация завершённой офлайн-Phase D

- Commit `dd278e5ac94c3c06fb8a617164fd5925cc92d284` успешно опубликован в origin/master; HEAD и remote-tracking ref совпали, working tree после публикации был чистым.31 изменённый текстовый файл прошёл UTF-8, JSON/локальные ссылки, staged diff check, проверку отсутствия binary/game/save payload и private deployment token. SHA исходников в Git index совпали с exact manifest; profile SHA совпал с pinned index и plan.
- После дополнительного guard против незарегистрированного content mod повторно прошли36 integrated tests и compileall; полный suite685/684 PASS/1skip указан выше. Ничего в пакете, игре, сохранениях, backup или карантинах эта доработка не изменяла: guard относится к будущему read-only writer-state аудиту Python.
- Пользователю подготовлен запрос отдельного разрешения на Phase E: установка только16 файлов из опубликованного exact manifest, повторный preflight/backup check, новый receipt, installed hashes и rollback dry-run, без запуска game/server или NPC. Phase F и spawn не разрешены. Ожидание этого разрешения — следующий шаг; `spawn_ready=false`.

## 2026-11-18 — Phase E разрешена и выполнена

- Пользователь отдельно разрешил установку только16 файлов согласованного manifest. Повторных исследований не проводилось. Подготовлен установщик с exclusive creation/fsync, immutable per-file intent/verified journal, отказом при конфликте/изменении source/live process и без automatic rollback/resume.6 новых fixture tests PASS; никакие fixture failures не относятся к реальной установке.
- Реальный preflight PASS: build1287369/Steam26430625/depot7226436020230696061, profile/plan/archive/source SHA, accepted PARTIAL baseline137 game/23 LOCAL, clean backup27/27; destinations16/16 отсутствовали, unknown files/links/shadow отсутствовали. Game/server closed и Steam idle проверялись до, между копиями и после.
- Установлены ровно16 approved files в `D:\SteamLibrary\steamapps\common\Enshrouded`; каждый source/destination повторно проверен. Пакет/plan/run binding не пересобирались. Создан новый receipt в `runtime/stage10_10_1_phase_e/20261118T122132276076Z/transaction/install-receipt.json`, SHA `c3cd5da70e01fd073553b6dcc2598e8ede867693087b67c285d65253c59d70fc`. Новый current-build rollback dry-run по реальной установке PASS16, откат не выполнялся.
- После установки полный inventory ровно153=137+16; все137 оригиналов, включая EXE/KFC/resources/64 DAT, и23 LOCAL совпали с baseline по SHA/размеру/mtime. Backup27/27 повторно PASS; inventories прежней копии и обоих карантинов совпали до/после. Ошибок установки/блокировки защиты не было, защиту не меняли. Игра/server/DLL не запускались, spawn/игровые команды не выполнялись.
- Full Python suite691 testsRun/690 PASS/1 прежний skip/0 failures,14.254s; compileall новых файлов PASS. Lua/package/native не менялись и не пересобирались. Готов отчёт Phase E, публичные metadata receipt/result/dry-run без private token и бинарников. Verdict READY_FOR_PHASE_F_APPROVAL; runtime NOT_EXECUTED/render UNKNOWN/spawn_ready=false. Следующий шаг — публикация результатов, затем отдельное согласование Phase F, не автоматический запуск игры.

## 2026-11-18 — результаты Phase E опубликованы

- Commit `7da512b2250e5ffd59b42157da4abb95d23da521` успешно отправлен в origin/master; HEAD/remote-tracking ref совпали, working tree после push был чистым.12 текстовых файлов прошли diff/staged check, UTF-8/JSON/локальные ссылки и проверку отсутствия private token и бинарников. Публичная копия receipt имеет тот же SHA, что локальный transaction receipt.
- Установка завершена без ошибок,16/16 и rollback dry-run PASS;137 оригиналов/23 LOCAL неизменны. Phase F готова к отдельному согласованию, но пока не разрешена. Игра/server не запускались, runtime NOT_EXECUTED и spawn_ready=false. Следующий шаг — дождаться разрешения на контролируемый load-only тест; автоматических действий больше не выполнять.

## 2026-11-18 — Phase F разрешена, preflight до ручного запуска PASS

- Пользователь разрешил контролируемый load-only Phase F, запуск/закрытие игры только вручную. Spawn/despawn/entity/faction/inventory/automatic rollback запрещены. Повторного исследования API не проводилось; использованы подготовленные validators.
- Fresh preflight `2026-11-18T12:29:31.689254+00:00`: build1287369/Steam26430625/depot7226436020230696061, game/server closed,Steam idle; pinned plan/profile/package/binding/receipt и installed16/16 PASS; backup27/27 PASS.137 originals/23 LOCAL SHA/size/mtime неизменны; inventory153 exact,unknown files/reparse/preexisting links/shadow отсутствуют. Rollback dry-run16 PASS без исполнения.
- До запуска сохранены67 resource identities/hash/link counts и полный153 game/23 LOCAL snapshot в `runtime/stage10_10_1_phase_f/20261118T122931689254Z`. Content input fingerprint прежний. Файлы character0/world0 соответствуют принятому baseline и содержат Body Test/AI Body Test; slot1 подтверждён историческим runtime mapping. Это offline соответствие, текущий выбор LOCAL/slot/name ещё будет проверен через Bridge после загрузки.
- Создан read-only preflight script, syntax PASS и фактическое выполнение exit0. Полный suite повторно не запускался; helpers/Lua/installed package не менялись. Подготовлен checkpoint report и public metadata без save payload/private run token.
- Статус READY_FOR_MANUAL_START; runtime WAITING_FOR_MANUAL_START, итогового verdict нет,spawn_ready=false. Следующий шаг — ручной запуск пользователем через Steam, LOCAL Body Test / AI Body Test,slot1, сообщение «загрузился». После runtime diagnostics дождаться ручного закрытия и выполнить post-run integrity; никаких игровых мутаций или rollback.

## 2026-11-18 — Phase F: BLOCKED_CONTENT_BUILD, ожидание закрытия игры

- После сообщения «загрузился» выполнено read-only чтение логов; процесс Enshrouded PID174844, запуск 15:35:07 MSK. Копии сохранены в runtime/stage10_10_1_phase_f/20261118T122931689254Z/runtime-capture.
- EMF0.6.18 начал integrated build patch0.5.0 и остановился на AIC_PATCH:graph_changed. State built_at=2026-11-18T12:35:08Z,code=2,unloaded=true,truncated=false; fingerprint совпадает с preflight. Пустое errors[] не означает успех.
- Проверка объединяет animationGraph==expected и retargetData==nil; точная причина расхождения пока не установлена. Регистрация clone/writer/evidence v8/visual dependencies/redirection не подтверждены. На критической ошибке диагностика остановлена до вызовов Bridge/observer; текущие LOCAL имена/слоты через Bridge не проверены.
- Обновлён Phase F report. Код, receipt и установленные файлы не изменялись; тесты повторно не запускались, игровые команды/rollback не выполнялись. spawn_ready=false.
- Следующий шаг: пользователь вручную закрывает игру и сообщает «закрыл», затем post-run integrity originals/installed/LOCAL, итоговый отчёт и публикация GitHub. Phase F ещё не завершена; неизменность файлов после запуска пока не заявляется.

## 2026-11-18 — Phase F завершена: post-close integrity и неудачный load-only тест

- Пользователь закрыл игру. Read-only аудит 12:42:29 UTC подтвердил отсутствие game/server, прежний Steam build, installed16/16, pinned package/receipt и clean backup27/27 SHA PASS.
- 67/67 original EXE/KFC/resources/64DAT сохранили SHA/size/identity/mtime. Ожидаемые56 shadow hardlinks подтверждены, лишних связей/reparse нет. Shadow66:56 links+3 private indexes+3 mod copies+3 cache+state; hashes indexes равны baseline, mod copies равны установке. Это не подтверждение writer/clone.
- Game inventory222:69 additions (shadow66+3 logs), удалений нет; содержимое прежних файлов изменилось только у3 logs. LOCAL23:17 неизменны по содержимому,6 изменились (character0/world0 и их backup-0/1); local_settings поменял metadata при прежнем SHA. Опубликованы before/after hashes без save payload. Агент saves не менял, семантическая целостность KSD не доказана, восстановления не было.
- Content loader явно сообщает запуск игры без content после AIC_PATCH:graph_changed/code2. Lua host/observer/Bridge startup видны в core log, но запросы не выполнялись вследствие остановки на критической ошибке. A/H/R/V/B UNKNOWN,C PASS; evaluator LOAD_ONLY_UNCONFIRMED, blocker BLOCKED_CONTENT_BUILD, render UNKNOWN,spawn_ready=false.
- Добавлен read-only post-close script, фактическое выполнение PASS; полный suite691 testsRun/690 PASS/1skip/0failures,12.433s. Обновлены README, Phase F report и public metadata. Исторический rollback dry-run не выдаётся за актуальный после создания shadow; rollback не выполнялся. Игровые файлы/сохранения не исправлялись, backup/quarantine сохранены.
- Следующий шаг: публикация этих результатов в GitHub и остановка. Требуется отдельная офлайн-диагностика graph/retargetData assertion; новая установка, игровой запуск и spawn не выполняются.

## 2026-11-18 — Stage10.10.2: офлайн-кандидат0.5.1 подготовлен

- Прочитаны ТЗ, AGENTS, Phase F report/logs/state/audits и закреплённый чистый EMF fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/vendor EML. Причина retarget assertion установлена по converter: Reference(Guid::NONE) становится zero GUID string в Lua, но JSON decoder выдаёт null. Старый fixture использовал nil. Runtime-значения прошлого запуска отдельно не захвачены; изменение самого graph не доказано.
- Исторический0.5.0 сохранён. Новый experimental/integrated_humanoid_0_5_1: строгие GUID strings, nullable nil/zero GUID, отказ на неизвестных типах без coercion, независимые ANIMATION_GRAPH/RETARGET_DATA ошибки и две AIC_GRAPH_DIAG_V1 строки до assert. Существующие source/clone/appearance/skeleton/HashKey32/faction/collision checks сохранены. Evidence8/Bridge1 прежние, версия явно проверяется новым binding.
- Подготовлен отдельный pinned compatibility profile, свежий run token, update manifest4 (mod.json/src/mod.lua/README/binding.lua), шаблон связанного update receipt, backup/rollback plans. Package dist/stage10_10_2_patch_0_5_1 проверен; DLL/observer code не меняются. Старый receipt immutable. Backup38 payload247154745 bytes (~247.2 MB) только запланирован, не создан.
- Native shadow rebuild подтверждён исходниками: новая версия/FILETIME меняют fingerprint; старый code2 с прежним fingerprint удерживается как KnownFailed, с новым выбирается BuildHeld. Manual cache cleanup не требуется, shadow66 с SHA/file IDs/links атрибутирован и сохранён. Новый fingerprint17d1f36b…8f1138 пока projected, должен пересчитываться при update; actual failed-state fingerprint87af1e89…419e воспроизведён точно. Реальный rebuild не выполнялся.
- Full suite714 testsRun/713 PASS/1skip/0failures,12.047s;23 новых regression tests. Lua syntax20/20 и compileall PASS. Actual candidate update+16 effective hashes+rollback dry-run4 проверены только на isolated fixture. Decoded-source fixture82 components/63 deps/18 refs/102 joints с zero-reference прошёл; resource API/clone/scan замоканы, vendor DLL и runtime не запускались.
- Повторный полный аудит:222 game/23 LOCAL records точно равны post-close snapshot, включая67 original resources/66 shadow/16 installed; backup27/27 SHA PASS. Шесть LOCAL-файлов, изменившихся в Phase F, приняты как текущая база и снова не менялись. Игра/server закрыты; backup/quarantine сохранены, rollback/cleanup/installation/mutations не выполнялись.
- Итог READY_FOR_PATCH_UPDATE_APPROVAL. Новый runtime_validation=NOT_EXECUTED,RUNTIME_RENDER_CONFIRMED=UNKNOWN,spawn_ready=false. Готов docs/STAGE10_10_2_REPORT.md и TEST_RESULTS. Следующий шаг: публикация GitHub, отдельное разрешение на backup/update4; затем отдельно повторный ручной load-only тест. Фактическая совместимость serializer/writer/render ещё не подтверждена; полная готовность live rollback не заявляется.
- Packaging correction перед публикацией: profile JSON нормализован в LF до вычисления SHA; CRLF-кандидат сохранён в runtime/stage10_10_2/superseded-crlf-candidate. Финальный пакет пересобран с новой привязкой, hashes/profile/Lua syntax/effective16 и rollback fixture4 повторно PASS; projected fingerprint прежний (размеры/FILETIME прежние). Установка игры не затронута.

## 2026-11-18 — update0.5.1 разрешён; проверенный механизм транзакции

- Пользователь явно разрешил backup38/~247.2 MB и обновление только4 файлов exact manifest, с receipt/effective16/fingerprint/post-integrity/rollback dry-run, без игры/spawn/ручной очистки/автоматического rollback.
- Добавлен исполнитель с pinned inputs, новым backup и immutable журналом intent/verified, exclusive temporary files, SHA/mtime/identity checks перед replace, остановкой при ошибке и сохранением частичного состояния. Receipt создаётся только после post-update audit. Ни receipt, ни прежний пакет не исправляются вручную.
- Новые7 transaction tests PASS: backup/replace, partial failure без rollback, backup tampering/source mismatch, отсутствие authorization, game live guard и hardlink refusal. Полный suite721 testsRun/720 PASS/1skip/0 failures,12.549s,exit0. Py_compile и diff check PASS.
- Исполнение реальной транзакции начато после тестов: начальный precheck closed/build/16 files PASS; полный baseline audit выполняется. Этот checkpoint ещё не означает успешную установку. Следующий шаг — завершить разрешённую транзакцию и записать фактический результат.

## 2026-11-18 — установка0.5.1 STOPPED: BLOCKED_BACKUP_PLAN_PATH

- Реальный preflight: game/server closed, build прежний, package/profile/binding/parent receipt/current16 PASS. Full baseline222 game/23 LOCAL точен, включая67 originals/66 shadow; старый fingerprint совпал, clean backup27 SHA PASS.
- Backup остановлен на38-й записи: project path compatibility\migration\1287369\phase_e\install-receipt.json содержит Windows backslashes, запрещённые recovery.target. Источник — прежний генератор backup plan использовал str(relative_path), а не as_posix. Это ошибка подготовленного плана, не антивирус/права. Условия safety validator не ослаблялись, approved plan не исправлялся на месте.
- Созданы37 копий/247144644 bytes в runtime/backups/stage10_10_2-patch-0.5.1-20261118T132845581508Z; повторная проверка их SHA/size PASS37. Backup manifest не создан: это partial backup, не completed verified38. Partial directory сохранён; старые backups/quarantines не изменялись.
- Replacement journal отсутствует,0/4 замен; update receipt не создавался. Установлен0.5.0,16 старых hashes повторно PASS. Нет update rollback dry-run по фактической установке, поскольку update не выполнялся; исторический fixture PASS не подменяет этот результат. Retry/rollback/cache cleanup не выполнялись.
- Полный post-stop audit13:30:51 UTC:222 game/23 LOCAL records точно равны before, включая67 originals/66 shadow. Агент не изменил игру/LOCAL; игра/server не запускались, spawn не выполнялся. Необходимость исправления backup plan не означает ошибку patch0.5.1 Lua.
- Готов docs/STAGE10_10_2_INSTALL_REPORT.md, обновлены README/предыдущий отчёт/TEST_RESULTS, опубликованы metadata failure/result без payload. Unit suite721/720 PASS/1skip не покрывал separator конкретного38-entry manifest; реальное выполнение корректно отказало.
- Статус BLOCKED_BACKUP_PLAN_PATH, повторный load-only пока не готов. runtime_validation=NOT_EXECUTED,RUNTIME_RENDER_CONFIRMED=UNKNOWN,spawn_ready=false. Следующий шаг — отдельно подготовить reviewed backup-plan revision с POSIX path и upfront validation всех38 entries; после согласования новая попытка, сохранив37 partial copies. Текущая попытка остановлена по явному условию пользователя; дальнейших установочных действий нет.

## 2026-11-18 — backup path исправлен; patch0.5.1 установлен

- Генератор переведён на .as_posix(); исходный план сохранён, создан revision2 SHA6b55956af459d8d3d82daa6c383740a4517a12e689d013ad3716271a2b05208a. Исполнитель закрепляет новый hash в коде и receipt. Все38 путей/групп/дубликатов/размеров/SHA проверяются до mkdir/copy; прежние валидаторы сохранены. Game payload и exact update manifest не менялись.
- Partial37 повторно проверен по точному составу/SHA/size. Первоначальный диагностический glob посчитал также каталог .cache; до установки остановились, read-only проверка только файлов подтвердила37/37. Manifest отсутствует, resume контрактом запрещён: partial сохранён, выбран новый backup.
- Полный preflight закрытой игры/server: pinned inputs/current16/clean backup27, baseline222 game/23 LOCAL, originals67/shadow66 и старый fingerprint PASS. Новый verified backup38/247154745 bytes создан и проверен до и после update: runtime/backups/stage10_10_2-patch-0.5.1-20261118T133801929065Z; manifest SHA eb7d81b857650c34f9f46d5040e21a033722fb5394b20e0fa4565c0eacc51208.
- Разрешённые4 файла обновлены,16 effective hashes PASS. Actual fingerprint sha256:17d1f36bb57e8dd9fc064eee5402ed4f10365d9970bda8fa975e7156638f1138. Полный post-audit подтвердил218 остальных game records,67 originals,66 shadow и23 LOCAL неизменными по SHA/size/identity/mtime/links. Parent receipt и старые backup/quarantine сохранены.
- Созданы immutable journal и новый receipt SHA8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053; public metadata в compatibility/updates/1287369/0.5.1/installation. Rollback dry-run4 PASS; full live rollback/shadow cleanup не заявляется, отката не было.
- Новые8 regression tests; полный suite729 testsRun/728 PASS/1skip/0failures,15.748s; py_compile/diff check PASS. Подробности в docs/STAGE10_10_2_INSTALL_REPORT.md. Подготовлена публикация исходников/тестов/отчёта без игровых payload и private token.
- READY_FOR_REPEAT_LOAD_ONLY_APPROVAL; game/server не запускались, spawn/mutations/cache cleanup не выполнялись. Старый failed shadow сохранён; штатная пересборка, graph/writer/evidence/render ещё не проверены. runtime_validation=NOT_EXECUTED,RUNTIME_RENDER_CONFIRMED=UNKNOWN,spawn_ready=false. Следующий шаг — отдельное разрешение на повторный load-only, новый preflight и ручной запуск пользователем.

## 2026-11-18 — повторный load-only0.5.1: preflight PASS

- Пользователь разрешил повторный load-only, ручной запуск/закрытие, read-only диагностику и post-close audit. Запрещены spawn/mutations/manual cache cleanup/automatic rollback.
- Новый scripts/preflight_patch_0_5_1.py использует существующие валидаторы; py_compile и фактический запуск exit0. 13:44:35 UTC game/server closed, build прежний, pinned inputs/receipt/current16 PASS, verified backup38 и clean27 PASS, rollback dry-run4 PASS без выполнения.
- Full inventory222 game/23 LOCAL точно совпал с post-install snapshot по SHA/size/identity/mtime/links; originals67/shadow66 неизменны. Fingerprint17d1f36b…8f1138 совпал. LOCAL Body Test/AI Body Test подтверждены baseline SHA и одним вхождением имени в character0/world0; текущий runtime slot/context пока требует Bridge.
- Сохранён checkpoint runtime/stage10_10_2/load_only/20261118T134435140530Z; inventory SHAfa172fc1c270ac4cd5751fdc185211149d8053adac8227fa03b1aa46d3204d18. Public preflight и docs/STAGE10_10_2_LOAD_ONLY_REPORT.md подготовлены к GitHub. Исторический suite728 PASS/1skip не запускался повторно; payload/валидаторы не менялись.
- READY_FOR_MANUAL_START. Игра не запускалась агентом; runtime_validation=WAITING_FOR_MANUAL_START,spawn_ready=false. Старый failed shadow сохранён. Следующий шаг — пользователь запускает LOCAL Body Test / AI Body Test и сообщает «загрузился»; затем runtime checks и после «закрыл» integrity audit и итоговая публикация.

## 2026-11-18 — load-only0.5.1: BLOCKED_BRIDGE_ACCESS, ожидание закрытия

- После сообщения «загрузился» обнаружен enshrouded PID187928, старт16:46:13 MSK. Скопированы content/loader/core/file_opens logs, state/shadow.txt в runtime/stage10_10_2/load_only/20261118T134435140530Z/runtime-capture. Игра запущена пользователем.
- Fresh content build13:46:15 UTC завершился code0,unloaded=true,truncated=false,errors/warnings пусты, patch0.5.1 и fingerprint совпали. Строгие existing evidence v8 parse и validate_state PASS. AnimationGraph GUID402df515-5965-4b01-a17b-17d482a91af4 PASS; retargetData userdata field string ZERO_GUID нормализован в null, PASS. Ошибка graph_changed предыдущего запуска здесь не повторилась.
- Evidence подтверждает регистрацию clone через EML_APP_STATE_AFTER_CREATE,82 components/fingerprint5253f478,9 HashKey32 source/clone,63 resolved dependencies,102 joints,18 visual references,source_unchanged=true. Это build evidence, не отображение или runtime lookup. Writer завершён по свежему state отдельно от REQUESTED_NOT_FINALIZED внутри build evidence. Loader сообщает штатную shadow rebuild и чтение shadow; независимый readback/redirection ещё не проверены.
- Единственная попытка existing integrated_observe compare остановилась при connect к pipe emf-bridge-187928: Windows error5 (access denied). hello/state и observer команды не выполнены. Причина/ACL/sandbox/лимит клиентов не определены; текст библиотеки про8 клиентов не является диагнозом. Повторного подключения/escalation/изменения прав нет согласно условию остановки при ошибке.
- BLOCKED_BRIDGE_ACCESS; A/H PASS (build),V REFERENCES_ONLY; B/R/C UNKNOWN до runtime/post-close проверок. LOCAL текущий runtime selection не подтверждён. Snapshot до запуска сохранён, post-close integrity ещё не выполнен. Игровых мутаций/spawn/cleanup/rollback не было; spawn_ready=false,renderUNKNOWN.
- Обновлён отчёт, подготовлена публикация промежуточного результата. Код не менялся, тесты повторно не запускались. Следующий шаг — пользователь закрывает игру вручную и сообщает «закрыл»; затем post-close аудит originals/installed/shadow/LOCAL и окончательный отчёт. Load-only успех не заявляется.

## 2026-11-18 — load-only0.5.1 закрыт; post-close audit и итог

- Пользователь закрыл игру. Повторный read-only audit13:50:45 UTC: game/server closed, build/pinned package/profile/binding/receipt PASS; installed16/16 и verified backup38/38 PASS. Все67 originals EXE/KFC/resources/64DAT неизменны по SHA/size/identity/mtime/links; fingerprint0.5.1 прежний.
- Inventory234 против222:12 additions/no removals. Shadow77 против66:9 generated DAT055–063, cache/files.json и shadow.txt; private KFC/resources/state и3 mod copies изменены штатным build. Mod copy hashes равны installed;56 base links подтверждены, private hardlink/reparse ошибок нет. Семантический readback не выполнен, полный shadow integrity PASS не заявляется.
- Audit STOPPED POST_CLOSE_BLOCKED: UNATTRIBUTED_NON_SHADOW_CHANGES — новый backup/enshrouded_2026-11-18T16-46-15.log и metadata-only изменение emf/chain_status.txt. SHA chain_status прежний. Это отсутствие атрибуции в точном allowlist исполнителя, не доказательство повреждения. Список не расширялся после ошибки, повторного обхода блокера нет.
- LOCAL23:7 content changes (character0/world0 и5 backup),16 прежних SHA/size; local_settings.json metadata-only; additions/removals нет. Before/after records опубликованы без save payload. Агент saves не писал/не восстанавливал; семантическая целостность KSD неизвестна.
- Результат compatibility/updates/1287369/0.5.1/load-only/post-close.json; private checkpoint post-close-20261118T135045278853Z. Обновлён docs/STAGE10_10_2_LOAD_ONLY_REPORT.md. Новый read-only audit wrapper использует существующие валидаторы; py_compile PASS. Полный suite729 testsRun/728 PASS/1skip/0failures,16.603s; лог runtime/stage10_10_2/load-only-post-close-tests.log. Unit PASS не отменяет фактический audit blocker.
- Итог LOAD_ONLY_UNCONFIRMED: A/H/C PASS,V REFERENCES_ONLY,R/B UNKNOWN. Build0.5.1/graph/retarget/evidence/writer подтверждены; BLOCKED_BRIDGE_ACCESS error5 не устранён, observer/LOCAL runtime context/shadow readback/independent redirection/render неизвестны. Spawn/mutations/cache cleanup/rollback не выполнялись,spawn_ready=false. После публикации остановка; следующий шаг — отдельно разобрать Bridge access и атрибуцию двух файлов, без нового игрового запуска сейчас.

## 2026-11-18 — Stage10.10.3: offline validation завершена, Bridge runtime pending

- Прочитаны ТЗ/AGENTS/PROGRESS/Stage10.10.2 report. Использованы закреплённые EMF fa6efdac2d93dd1d8ac6fe0e2a658140aec35241 и существующий KFC Inspector SHA81531333e5b73d7c1fed55dcfb8284c874deb2e4f84a6a68dbe4bed79314f075. Новых исследований уже подтверждённых API, сборки native DLL/patch и запуска игры не было.
- Current Python token: codexsandboxoffline, restricted=true, Medium, elevated=false/AppContainer=false. EMF DACL допускает только game user/SYSTEM и integrity>=game. Sandbox отдельной учётной записи — подтверждённый фактор и наиболее обоснованное объяснение error5; SID/ACL уже закрытого PID187928 не сняты, окончательная историческая причинность не заявляется. WMI explorer owner из sandbox отказал; ACL/UAC/security не менялись, эскалации диагностики не было.
- Vendored Bridge отличается от pinned0.6.18 только текстовой подсказкой load_world, транспорт/протокол совпадают. Vendor не менялся; wrapper получил классификацию error5/2/3/231/121/109/233 без утверждения про8 клиентов. Подготовлен scripts/diagnose_bridge_access.py: текущий token реально проверен, live путь только подготовлен (token game/client, ACL read, hello/state, stop-on-error). План — обычный PowerShell пользователя игры после отдельного согласования, без admin/ослабления ACL.
- Post-close validator v2 PASS: конкретный архивный лог полностью равен старому enshrouded.log включаяfileID/mtime (rename); новый лог другойidentity. Chain_status пустой, прежниеSHA/identity/links, толькоmtimeвсессии; EMF loader source подтверждает wb при старте. Неизвестные backup/emf изменения, содержание/identity/hardlinks не разрешены. Исторический blocked JSON сохранён; новая оценка отдельно.
- Независимый KFC readback source-original/source-shadow/clone/hierarchy/presets +63 typed GUID lookups PASS. Полное сравнение82 компонентов разрешает толькоname/faction/npcId; PlayerAlly/npcId2939921867/GUID/9HashKey32/graph/retarget/RenderEquipment/пропорции/102joints/18visual references подтверждены. Source canonical SHA совпал с pinnedprofile; hierarchy/presets целиком равны clean baseline. Один GUID может иметь несколькоtypes; проверяется точная composite identity.
- Database audit:12270 decoded templates,91910index rows,101492contentrefs,59chunks,0duplicates; ровно1npcIdmatch=clone. DAT055–063 —9private пустых файлов0bytes, не доказательство визуального payload. Exact shadow77,56basehardlinks,privateindexes/modcopies/cache/metadata и shadow.txt/sourceFILETIME проверены существующим audit_shadow. State/fingerprint/writer PASS.
- Resource redirection: сохранённый log16:46:15 подтверждает успешный GENERIC_READ/OPEN_EXISTING CreateFile для66 KFC/resources/DAT000–063 черезshadow. Это фактические открытия длячтения, не tracing ReadFile bytes и неrender.
- Финальный audit14:05:36 UTC: game/server closed, original67/installed16/backup38 PASS; все234game/23LOCAL records до/послеисследования точносходятся, SHA обоихsnapshot9bb5ef6895915469d1e35a302b2071f2037348049f4f07e0178c39a3237ae904. Использован актуальный post-close baseline с7изменённымиLOCAL; savesнеизменялись, новыхbackupнет.
- Добавлены29regressiontests; fullsuite758 testsRun/757PASS/1skip/0failures,16.179s; compileall companion/scripts/tests иdiffcheckPASS. Результаты compatibility/updates/1287369/0.5.1/stage10_10_3/result.json, docs/STAGE10_10_3_REPORT.md; dumps/rawSID остаютсяprivate runtime/stage10_10_3.
- Итог LOAD_ONLY_UNCONFIRMED: A/H/R/C PASS,V REFERENCES_ONLY,B UNKNOWN. Осталась успешная runtime Bridge/observer/context проверка; RUNTIME_RENDER_CONFIRMED=UNKNOWN,spawn_ready=false. После commit/push остановка до отдельного разрешения. Игру/server/NPC не запускали; установленныйpayload, права, shadow/cache иLOCAL не меняли, rollbackнеисполнялся.

## 2026-11-18 — Stage10.10.3 runtime continuation: свежий preflight PASS

- Пользователь разрешил завершение load-only, адресные read-only диагностические команды вне ограниченного sandbox через штатное согласование; запуск/закрытие игры только пользователем. При недоступности — готовая PowerShell-команда. Spawn/mutations/rollback/изменение модов и прав запрещены.
- Существующий preflight получил явный режим --stage10-10-3 с pinned Stage10.10.3 result и актуальным post-close snapshot SHA9bb5ef6895915469d1e35a302b2071f2037348049f4f07e0178c39a3237ae904. Исторические checkpoint не менялись; в baseline входят7 LOCAL-файлов, изменённых предыдущей игрой.
- Реальное выполнение14:12:27 UTC exit0: game/server closed, build/pinned inputs/receipt/installed16, verified backup38 и clean backup27 PASS; file-only rollback dry-run4 PASS, не выполнен. Full game234/LOCAL23 точно совпали с baseline по SHA/size/identity/mtime/links, включая originals67/shadow77. Fingerprint0.5.1 совпал. Inspector/readback исследования повторно не выполнялись.
- LOCAL Body Test character0 и AI Body Test world0 подтверждены актуальными SHA и именами; runtime slot/storage/name пока требует Bridge. Private checkpoint runtime/stage10_10_3/load_only/20261118T141227374049Z, public preflight в compatibility/updates/1287369/0.5.1/stage10_10_3/load-only. Py_compile/diff check PASS, полный suite повторно не запускался.
- READY_FOR_MANUAL_START. Game/server не запускались, установленные файлы/права/сохранения не менялись. Успешный cache0.5.1 сохранён. Следующий шаг — пользователь загружает LOCAL Body Test / AI Body Test и сообщает «загрузился»; далее адресный diagnostic/hello/state/observer compare, затем после закрытия audit v2. runtime_validation=WAITING_FOR_MANUAL_START,spawn_ready=false,RUNTIME_RENDER_CONFIRMED=UNKNOWN.

## 2026-11-18 — Stage10.10.3: Bridge и observer в загруженном мире PASS

- Пользователь сообщил «загрузился»; PID202212, ручной запуск17:15:49 MSK. Адресная read-only диагностика вне sandbox одобрена штатным механизмом: одинаковый пользователь, достаточный integrity, pipe security READ; hello/state PASS, EMF0.6.18/API46/protocol1/build1287369. ACL/права не менялись; rawSID/private tokens не публикуются.
- Observer compare/status PASS: nonce/binding/profile/session, LOCAL Body Test slot1 / AI Body Test slot1, active Lua1.39.0 + observer0.3.0, evidence v8 40/40 полей. Контекст до/после совпал. Только read-only команды.
- Loader использует существующий успешный cache0.5.1 от13:46:15 UTC; state SHA равен preflight, code0/unloaded=true, warnings/errors пусты. Свежий rebuild не заявляется; прошлый readback не повторялся, post-close проверка shadow ещё предстоит.
- Свежий file-open log17:15:49: успешные перенаправленные открытия для чтения66/66 KFC/resources/DAT. Разовый офлайн wrapper ошибочно ожидал имя enshrouded.kfc.resources; после сверки существующего контракта исправлено на enshrouded.kfc_resources на той же сохранённой копии лога, PASS. Валидатор не менялся, повторных live запросов из-за этого не было. ReadFile bytes/render не доказаны.
- Сохранены private capture/diagnostic/observer и public runtime-checkpoint.json; отчёт docs/STAGE10_10_3_REPORT.md обновлён. Исполненные существующие runtime валидаторы PASS; unit suite повторно не запускался (код не менялся).
- RUNTIME_READ_ONLY_CHECKS_PASS_AWAITING_MANUAL_CLOSE. Общий load-only verdict ожидает post-close audit v2 оригиналов/16 installed/77 shadow/LOCAL относительно baseline. Spawn_ready=false, runtime_render=UNKNOWN. Следующий шаг: пользователь закрывает игру и сообщает «закрыл». Игра/server/NPC агентом не запускались, игровые файлы/сохранения не менялись, rollback не выполнялся.

## 2026-11-18 — Stage10.10.3 завершён: LOAD_ONLY_SUCCESS после post-close audit v2

- После сообщения «закрыл» проверены закрытые game/server и Steam build/depot/idle. Новый read-only wrapper scripts/audit_stage10_10_3_closed.py использует существующие snapshot/audit_shadow/reassess_post_close/verify_updated/verify_backup/evidence/redirection validators; никаких установок, запусков, мутаций и rollback.
- Реальный audit завершён14:25:40 UTC: installed16/16, verified backup38/38, originals67/67 PASS. Все77shadow records точно совпали с preflight и pinned предыдущим readback; audit_shadow PASS,56допустимыхhardlinks. Inspector/предыдущие исследования не повторялись. Fingerprint0.5.1 прежний; cache13:46:15UTC использован штатно, fresh rebuild не заявляется.
- Post-close v2 ATTRIBUTION_PASS: новый архивbackup/enshrouded_2026-11-18T17-15-49.log является точным rename предыдущего лога;4текущихлога изменились, пустойchain_status толькоmtimeвсессии. Необъяснённых изменений нет, game inventory235. Историческаяgraph_changed в накопительномloaderlog не относится к текущемуcache reuse.
- LOCAL23/23 существуют, непустые, стабильны при повторном чтении;6файлов изменили содержимое за игровуюсессию (character0/world0+по2backup),local_settings толькоmetadata;17содержимых совпали. ИменаBody Test/AI Body Test сохранены. Семантическая целостность saveформата не установлена; хешидо/после записаны. Агент savesнеписал/невосстанавливал.
- Runtime предыдущего checkpoint успешно связан с post-close: Bridgehello/state,observercompare/status,LOCALslot1/context/session PASS; evidencev8 40/40;66/66 свежихread-openчерезshadow. Итог A/H/R/B/C PASS,V REFERENCES_ONLY; LOAD_ONLY_SUCCESS. Render/поведениеNPCнепроверены,ReadFilebytesнетрассировались,spawn_ready=false. ПринятоеограничениеCLEAN_BASELINE_PARTIALсохраняется.
- Fullsuite повторно выполнен:758testsRun/757PASS/1skip/0failures,16.089s. Skipdirectorysymlink:WinError1314,права не менялись. Py_compile/diffcheckPASS. Отчёт docs/STAGE10_10_3_REPORT.md; public post-close.json/tests-post-close.json в compatibility/updates/1287369/0.5.1/stage10_10_3/load-only. Privatepost-close-20261118T142336157270Z; inventory SHA после2fe87275d6c666bdf8aae2ba810cc606e2a52e1daeb4d95ccbf19d86f60a4987. Бинарники,сырыелоги,SID/tokens/сохранениянепубликуются.
- Следующий шаг: commit/push результата и остановка. Новые игровые испытания/spawn требуют отдельного разрешения; моды/ACL/cache/shadowнеизменялись,автоматическогоrollbackнет.

## 2026-11-18 — Stage 10.11: офлайн-подготовка первого humanoid spawn

- Прочитано ТЗ и актуальные Stage 10.10.3 / 10.8 / 10.9 safety материалы. По закреплённому EMF 0.6.18 (fa6efdac2d93dd1d8ac6fe0e2a658140aec35241) проверены ground_at/path_find/find_wall/spawn/spawn_ex, world components/session и существующие Companion/Beastmaster/Villager Jobs. Новые ground/path API достаточны для ограниченного disposable visual experiment с ручным осмотром; production ownership/cleanup не объявлены решёнными. Native extension не создавался.
- Добавлен изолированный aic_first_spawn 0.1.0 (Lua controller/main), отдельный Python client/CLI и read-only gate receipt/backup. Только fixed GUID, LOCAL Body Test / AI Body Test slot 1, один player и один API attempt; explicit authorization + visual/persistence acknowledgments, freshness/session/context gates, запрет повторов. Python fsynced exclusive intent и Lua persistent UNUSED→SPENT latch; отказ/0/timeout/reload не разрешают retry. Destroy/faction/teleport/respawn/follow/combat/inventory отсутствуют. Observer и patch 0.5.1 не менялись.
- Свежий read-only preflight: closed game/server, build/depot/idle, installed16 PASS; все 235 game / 23 LOCAL records точно совпали с последним post-close baseline SHA2fe87275d6c666bdf8aae2ba810cc606e2a52e1daeb4d95ccbf19d86f60a4987. Новые destinations отсутствуют. KFC readback/прошлые исследования не повторялись.
- Подготовлен dist/stage10_11_first_spawn_0_1_0: ровно 7 новых файлов, без DLL/EXE/EML изменений. Exact manifest SHA6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3, public compatibility/experiments/stage10_11. Backup plan: 23 LOCAL-файла, 637447 bytes; предварительная валидация выполнена, сам backup НЕ создан. Пакет 7/7 SHA/size совпадает с исходниками; private key остаётся в ignored dist.
- 66 новых целевых тестов PASS. Полный suite выполнен:824 testsRun /823 PASS /1 skip /0 failures,14.964s. Skip прежний directory-symlink WinError1314; права не менялись. Compileall/diff check PASS. Private log runtime/stage10_11/full-tests.log; public tests.json.
- docs/STAGE10_11_REPORT.md содержит API sources, install/backup/receipt plan, команды будущего запуска, визуальный чек-лист, наблюдение30–60s, остановку при ошибке и post-close/restore plan. Закрытие игры не доказывает cleanup: ForceSave/ActiveNpcStateSaved/villager lifecycle могут сохранить NPC; полный LOCAL restore требует отдельного согласования. Render, мирный AI и фактический spawnability ещё UNKNOWN; generation/atomic destroy нет.
- Итог READY_FOR_EXPERIMENTAL_SPAWN_APPROVAL; experimental_spawn_executed=false,production_spawn_ready=false,spawn_ready=false,RUNTIME_RENDER_CONFIRMED=UNKNOWN. Установка/игра/spawn/despawn/game writes/save edits/rollback/ACL/cache cleanup НЕ выполнялись. Следующий шаг — отдельное разрешение на backup23 и установку7; сам spawn потребует непосредственного отдельного разрешения после live preflight. Commit/push и остановка.
- Финальная read-only проверка после подготовки: game/server закрыты; набор и метаданные всех235 game files прежние, повторные полные SHA/records LOCAL23 совпали. Полный hash оригиналов выполнен на preflight, в финальной проверке повторно не заявляется. Public JSON проверены, private deployment key не опубликован; final-read-only-check.json сохранён.

## 2026-11-18 — Stage 10.11: разрешённая установка и READY_FOR_MANUAL_START

- Пользователь разрешил backup23 LOCAL, только семь новых файлов aic_first_spawn0.1.0, receipt/removal dry-run/preflight; подтвердил disposable Body Test / AI Body Test. Spawn, автоматический rollback, изменение saves/существующих модов и запуск игры агентом запрещены.
- Добавлен additive installer с точным allowlist7, exclusive copy, fsync, intent/complete journal и stop-on-error без удаления; отдельный read-only preflight. Девять новых transaction tests PASS; полный suite833 testsRun/832PASS/1skip/0failures,15.986s. Skip прежний directory symlink WinError1314. Py_compile/diff check PASS.
- Read-only preflight и повторный preflight разрешённой установки: closed/build/depot/idle/package7/existing16/destinations PASS; полный baseline235 game/23 LOCAL совпал. Manifest неизменен: SHA6ecc792b6c320dc19f0fa201259c573efd142c4c37a579eab07376dc40b9e1e3.
- Создан verified backup runtime/backups/stage10_11-local-before-first-spawn:23/23 файла,637447bytes; manifest SHAc88339083683e9f6ce36aa2ab2fceb4bebcf9bdfe90926630e52422463011041. Источники и прежние backup/quarantine сохранены, restore не выполнялся.
- Реальная установка завершена14:51:46UTC: ровно7 новых файлов по manifest, существующие235 game records и23 LOCAL точно неизменны; originals67/shadow77/existing16 PASS. Новый inventory242 game. Private journal runtime/stage10_11/install/20261118T145106436795Z.
- Новый receipt compatibility/experiments/stage10_11/installation/receipt.json SHA3b9d80c0ade318c378584e38809eda54d6c4bc689ef16f1a5af28e5a993fd950. Старый receipt/план не редактировались. Read-only client installation gate PASS; removal dry-run7 PASS, не выполнен, неизвестные файлы/каталоги/saves/shadow исключены.
- Отдельный свежий preflight14:52:38UTC READY_FOR_MANUAL_START: receipt/backup23/installed23/latch UNUSED/removal PASS; полный post-install inventory SHA5f200502df076c1d2c81d126b4f6db5d10e9010f8f32cd682eb09b8117c1175a совпал, LOCAL имена подтверждены. Evidence installation/preflight/20261118T145238316160Z.json; live Bridge/context/position пока не выполнялись.
- docs/STAGE10_11_INSTALLATION.md и TEST_RESULTS.md обновлены. Мод включён отдельным ini, автоматического spawn нет. EMF/patch0.5.1/observer/ACL/cache/shadow/существующие моды/saves не менялись. Game/server/NPC агентом не запускались, spawn/despawn/rollback не выполнялись.
- Следующий шаг: пользователь вручную загружает LOCAL Body Test / AI Body Test slot1 и сообщает «загрузился», затем read-only live context. Spawn требует отдельного непосредственного разрешения. spawn_authorized=false,experimental_spawn_executed=false,production_spawn_ready=false,spawn_ready=false,RUNTIME_RENDER_CONFIRMED=UNKNOWN. Публикация и остановка.

## 2026-11-18 — Stage 10.11: read-only диагностика после ручной загрузки

- PID216444, Bridge hello/state PASS: EMF0.6.18/API46/build1287369; LOCAL Body Test / AI Body Test slot1/1, игрок жив. Активны только Lua1.39.0, observer0.3.0, aic_first_spawn0.1.0.
- Штатный experimental status с проверкой manifest/receipt/backup23/existing16 PASS: NEW, attempted=false. Observer status PASS, сессия совпала, контекст до/после неизменен. Повторные SHA семи новых файлов PASS, latch UNUSED, probe/spawn-intent отсутствуют.
- Первый hello/state вызов не сохранил отчёт из-за отсутствующего каталога; каталог создан в проекте, read-only проверка повторена успешно. Игровые мутации не выполнялись. Private evidence runtime/stage10_11/live/20261118-session216444; публичный отчёт docs/STAGE10_11_LIVE_CHECK.md.
- Диагностический журнал теперь существует (только status); не удалять и не считать автоматически признаком spawn. Позиция не проверена, spawn не разрешён/не выполнен; spawn_ready=false, production_spawn_ready=false, render UNKNOWN. Post-close audit ещё не выполнен. Unit-тесты повторно не запускались при изменении только документации.
- Следующий шаг: отдельное непосредственное разрешение пользователя на один экспериментальный spawn на открытом участке, затем свежий контекст и ground/path проверки; отказ любого условия запрещает spawn. Публикация отчёта и остановка.

## 2026-11-18 — Stage 10.11: разрешение spawn, остановка до создания NPC

- Получено непосредственное разрешение на один экспериментальный spawn. Повторные штатные проверки manifest/receipt/backup23/existing16 и LOCAL-контекста PID216444 прошли.
- Отправлен один prepare; пять read-only status с паузами0.5s оставались GROUND, ok=true, attempted=false. Исполнитель остановился с PROBE_NOT_READY_STOP до вызова spawn. Это локальный предел ожидания, не доказанный отказ API и не полный20s timeout Lua. Последнее наблюдаемое состояние GROUND; причина задержки callback неизвестна.
- После остановки проверены SHA7/7, latch UNUSED, отсутствие spawn-intent.json и наличие probe.json. Повторов, сброса журнала, spawn/observe/destroy/rollback/save edits/изменения модов не было. Private evidence runtime/stage10_11/live/20261118-session216444; docs/STAGE10_11_LIVE_CHECK.md дополнен. Unit-тесты повторно не запускались.
- Итог BLOCKED_BEFORE_SPAWN; experimental_spawn_executed=false, spawn_ready=false, production_spawn_ready=false, render UNKNOWN. Следующий шаг: пользователь вручную закрывает игру, затем post-close audit и разбор ground callback/окна ожидания. Журнал не удалять, автоматически probe/spawn не повторять. Отчёт публикуется в GitHub.

## 2026-11-18 — Stage 10.11: post-close audit и причина остановки

- Игра/сервер закрыты. Новый read-only scripts/audit_stage10_11_closed.py повторно использует pinned baseline текущей сессии, штатные install/backup/snapshot/post_close_v2 валидаторы. POST_CLOSE_INTEGRITY_PASS_SPAWN_NOT_EXECUTED; public compatibility/experiments/stage10_11/installation/post-close-216444.json, private runtime/stage10_11/live/20261118-session216444/post-close.
- Полный hash/identity audit: originals67 и shadow77 точно неизменны, installed23/backup23 PASS. Один новый файл — точный rename прежнего игрового лога; изменения остальных логов и mtime пустого chain_status атрибутированы v2, неизвестных изменений нет. LOCAL23 без добавлений/удалений, 8 content changes/9 metadata changes, имена тестового персонажа/мира сохранены; автосохранения зарегистрированы. Семантическая целостность saves не установлена, restore не выполнялся.
- Лог подтвердил GROUND_REQUESTED18:01:58.131 → READY18:02:02.642, через4.511s. Последний status был18:02:01.792, то есть за0.850s до READY. Частный исполнитель остановил ожидание слишком рано; отказ EMF не подтверждён. Ground/path успешно достигли READY позднее. Spawn-команды/attempt/entity-return отсутствуют; latch UNUSED, spawn-intent отсутствует.
- Полный suite833 testsRun/832PASS/1skip,0failures,13.959s, Python exit0. Первый запуск также сообщил OK15.762s, но PowerShell вернул NativeCommandError из-за stderr; повтор через subprocess установил реальный exit0. Py_compile и diff check PASS. Skip прежний directory-symlink privilege, права не менялись.
- docs/STAGE10_11_LIVE_CHECK.md обновлён. Игровые файлы/saves/моды/журнал probe не изменялись, reset/rollback/spawn не выполнялись. Следующий шаг — подготовить безопасное продолжение с сохранением истории probe и deadline в рамках20s, затем отдельное согласование следующего эксперимента. spawn_ready=false, production_spawn_ready=false, render UNKNOWN. Публикация результатов и остановка.

## 2026-11-18 — Stage 10.11.1: deadline Ground/Path и безопасное продолжение

- Выполнена только офлайн-подготовка. Lua Spawn Controller0.1.0, установленные моды, игровые ресурсы, сохранения и latch не изменялись. Игра/сервер не запускались, Bridge/probe/spawn/rollback не выполнялись. Исследования EMF/template/Bridge/shadow не повторялись.
- Новый companion/experimental_wait.py: ожидание GROUND/PATH по prepared_at+20s, polling250ms (допустимо250–500), monotonic bound/clock-change guard; READY/STOPPED/timeout/API errors обработаны без retry. READY проверяет nonce/session/player и остаток срока. Минимум8s для непосредственного подтверждения+2s send reserve; READY на15s распознаётся, но spawn запрещён из-за недостаточного времени. Срок не продлевается от READY. Реальная человеческая задержка не гарантируется; просрочка блокирует команду.
- ExperimentalClient повторно проверяет deadline после context/status и после записи request непосредственно перед отправкой spawn. Просрочка после durable intent оставляет глобальную блокировку. CLI prepare-wait только проверяет место/ожидает, никогда не вызывает spawn автоматически.
- ContinuationClient сохраняет старые17 файлов с pinned SHA, использует один заранее определённый attempts/uuid только в новой игровой сессии. Общий родительский spawn-intent блокирует все попытки/старый клиент; latch не сбрасывается. Повтор prepare и изменение истории запрещены. Private continuation-plan SHA5f31ce5a6fd718a73d52c7832b3d5f162b4969b075049affc662802e6f7aba0f.
- Актуальный post-close baseline8eefec278ddb2be742674c0010489a92fd9ba9d6495de7cbaf3efc127fd41094 повторно полностью совпал:243 game/23 LOCAL. Создан и проверен новый backup runtime/backups/stage10_11_1-local-before-new-probe:23/23,637431bytes; manifest SHAadebdf8e1e5b2433d270499402ff117d3246f70be48612a159f8a134a2015c6a. Источники перечитаны после backup, прежние backup/quarantine/receipt сохранены.
- Отдельный preflight_stage10_11_1.py: pinned plan/history/installed23/backup23/unused latch/full baseline PASS. Новый probe не начат. Runtime deadline и backup-проверки включены в CLI continuation. docs/STAGE10_11_1.md содержит команды и план, включая явное непосредственное согласие и post-close с новым PID/baseline.
-25 новых regression tests; полный suite858 testsRun/857PASS/1skip/0failures16.499s, Python exit0. Skip прежний directory-symlink privilege. Py_compile/diff check PASS. Результаты compatibility/experiments/stage10_11_1/tests.json; private log runtime/stage10_11_1/tests-final.log.
- Следующий шаг: отдельное согласование повторного игрового эксперимента, fresh closed preflight, ручной запуск пользователем, новый prepare-wait, непосредственное подтверждение лишь при достаточном остатке времени. Новое разрешение spawn не подразумевается подготовкой; spawn_ready=false, production_spawn_ready=false, render UNKNOWN. Код/отчёт публикуются в GitHub, затем остановка.

## 2026-11-18 — Stage 10.11.1: свежий preflight разрешённого повторного эксперимента

- Пользователь разрешил повторный игровой эксперимент с отдельным непосредственным разрешением spawn только после READY и достаточного времени. Игру запускает/закрывает только пользователь; запрещены автоматические повторы, destroy, изменение игровых файлов и rollback.
- Свежий closed preflight выполнен 15:58:11–15:58:43UTC, exit0: pinned continuation plan, installed23, verified backup23, неизменная история17, latch UNUSED и полный baseline243 game/23 LOCAL PASS. Игра/сервер закрыты; новый probe не начинался. READY_FOR_MANUAL_START. Evidence runtime/stage10_11_1/live/20261118T155811475946Z/preflight.json и preflight.log.
- Код не изменён; unit-тесты повторно не запускались. Игровые файлы/saves/latch/история не изменялись, Bridge/prepare/spawn/rollback не выполнялись; spawn_ready=false.
- Следующий шаг: пользователь вручную загружает LOCAL Body Test / AI Body Test slot1, сообщает «загрузился». Затем read-only Bridge/LOCAL/new session/NEW; перед prepare-wait отдельное предупреждение о готовности быстро подтвердить, после READY запрос непосредственного разрешения только при достаточном остатке времени. После ручного закрытия — post-close audit с новой сессией и публикация результатов в GitHub.

## 2026-11-18 — Stage 10.11.1: новая сессия, ожидание готовности пользователя к prepare-wait

- После ручной загрузки PID230172 (старт18:59:13 местного времени) выполнены только hello/state и continuation status. Bridge EMF0.6.18/API46/build1287369 PASS, LOCAL Body Test / AI Body Test slot1/1, player1 health100/100. Новая session отличается от предыдущей, controller NEW, latch UNUSED.
- CLI повторно проверил pinned install receipt/manifest, старый и новый backup через gates, pinned baseline и историю. В новом planned attempt только диагностический status; нового probe.json и общего spawn-intent.json нет. Private evidence runtime/stage10_11_1/live/20261118T155811475946Z/session230172; checkpoint.json с хешами ответов.
- prepare-wait/spawn/observe/destroy/rollback не выполнялись; игровые файлы/saves/latch не изменялись агентом. Unit-тесты не повторялись, код не менялся. spawn_ready=false.
- Перед prepare-wait пользователь предупреждён: выбрать открытое сухое ровное место, не двигаться и быть готовым быстро подтвердить после READY. Следующий шаг — сообщение «готов» как готовность к проверке места (не разрешение spawn), затем один prepare-wait; запрос непосредственного разрешения spawn только при READY и достаточном времени. Публикация итогов остаётся после ручного закрытия и post-close audit.

## 2026-11-18 — Stage 10.11.1: prepare-wait достиг READY

- После сообщения пользователя «готов» выполнен один prepare-wait для PID230172, exit0. Ground/Path достигли READY; на момент ответа осталось15.153s общего срока,13.153s для подтверждения с reserve2s; sufficient=true. Позиция x3698.80859375,y893.5009765625,z1282.035888671875. Штатный immutable ready-window.json сохранён в planned attempt.
- Немедленно отправлен отдельный запрос разрешения на однократный spawn через async UI. Подтверждение пока не получено; spawn НЕ выполнялся. Срок не продлевается; поздний ответ не разрешает обход deadline. Автоматических повторов/сброса latch/изменений игры нет. spawn_ready=false. Следующий шаг — своевременный ответ пользователя либо остановка по сроку.

## 2026-11-18 — Stage 10.11.1: подтверждение получено, deadline истёк до отправки spawn

- Пользователь ответил «Разрешаю один spawn» на запрос после READY. Выполнен один вызов штатного Python spawn CLI; client gate завершился PROBE_EXPIRED до durable spawn intent и до отправки console spawn. Задержка взаимодействия/запуска превысила оставшееся окно; контроллер не обходился, срок не продлевался.
- Проверено локально: общий spawn-intent отсутствует, в новой истории0 spawn-request, latch UNUSED. История probe/ready сохранена. Повторных попыток, destroy, rollback и изменения игровых файлов нет. Итог STOPPED_PROBE_EXPIRED_BEFORE_SPAWN, spawn_executed=false,spawn_ready=false. Evidence compatibility/experiments/stage10_11_1/probe-outcome-230172.json; private spawn-command.txt содержит traceback.
- Следующий шаг — пользователь вручную закрывает игру, затем новый post-close audit и публикация результатов. Для следующего эксперимента потребуется отдельно подготовить способ непосредственного подтверждения с меньшей задержкой в пределах неизменного контракта; автоматический retry или удаление истории не допускаются. Визуальная проверка/наблюдение NPC не проводились, поскольку NPC не создан.

## 2026-11-18 — Stage 10.11.1: post-close audit PID230172 и итог повторного эксперимента

- Игра/сервер закрыты. Новый read-only scripts/audit_stage10_11_1_closed.py использовал фактическую сессию, pinned baseline8eefec... и existing install/backup/snapshot/post_close_v2 валидаторы. Итог POST_CLOSE_INTEGRITY_PASS_SPAWN_NOT_EXECUTED; public compatibility/experiments/stage10_11_1/post-close-230172.json.
- Originals67 и shadow77 точно неизменны, installed23/backup23 PASS. Добавлен только точный rename предыдущего лога; штатные изменения логов/mtime chain_status атрибутированы, неизвестных изменений нет. LOCAL23 без добавлений/удалений, content8/metadata9 changed; имена сохранены, в логе9 world-save событий. Семантика saves не доказана, restore не выполнялся. Новый snapshot SHA6cd6ac15025cce3119236b1e52d998a5d850e86c95ec6eace16c1af70e9d23bf.
- GROUND_REQUESTED19:02:21.151 → READY19:02:25.661 (4.510s). Исправленное ожидание успешно. После ответа пользователя spawn CLI остановлен по PROBE_EXPIRED до intent/request/API. В новой истории один probe/ноль spawn-request; старые17 файлов неизменны; latch UNUSED. Причина остановки — задержка подтверждения/доставки/запуска сверх оставшегося окна, вклад компонентов не измерен.
- Реально повторены29 tests runtime_validation:29PASS,0failures,0.002s,exit0; py_compile/diff check PASS. Полный suite не повторялся. docs/STAGE10_11_1_RUNTIME.md содержит подробный отчёт, ограничения и evidence paths. Приватные логи/binding/saves не публикуются.
- Игру агент не запускал, моды/игровые файлы/saves не менял; повторов, destroy, сбросов истории/latch и rollback не было. spawn_ready=false,production_spawn_ready=false,render UNKNOWN. Визуальное наблюдение30–60s не проводилось, поскольку NPC не создан.
- Следующий шаг только после отдельного согласования: подготовить низколатентное непосредственное подтверждение в локальном процессе, сохраняя deadline, обе истории, свежий baseline/backup. Сейчас публикация отчёта в GitHub и остановка.

## 2026-11-18 — Stage 10.11.2: Local Interactive Spawn, офлайн-подготовка

- Реализованы companion/interactive_spawn.py и scripts/local_interactive_spawn.py: install/backup/history gates, PID/LOCAL/context, prepare/wait/локальная Y/spawn в одном процессе/Bridge-соединении. Чат и запуск нового subprocess для подтверждения не нужны. CLI агентом не запускался в live-режиме.
- Windows console проверяется до Bridge; msvcrt.getwch без Enter, буфер до READY отбрасывается, ранняя/удерживаемая Y не подтверждает. После READY выводятся координаты, требуется release+200ms quiet, приглашение и обратный отсчёт. СвежаяY — одно согласие, N/ESC — отмена; ввод во время wait может отменить между RPC. Pipe/non-console и extended-key ambiguity отвергаются. Реальные клавиши Windows в этом этапе не испытывались.
- Контракт20s от prepared_at, минимум8s+2s reserve, проверка времени после arming и перед отправкой, monotonic/clock guard, session validation и durable global intent сохранены. Local confirmation привязан кnonce; generic CLI не может обойти local key gate. Exclusive interactive-started запрещает повтор после отмены/ошибки/успеха. Latch и оба старых probe не сбрасываются.
- Новый plan runtime/stage10_11_2/continuation-plan.json SHA2d3cd9c0bbef8cd8135c2775fe1322296b8511bc5368e4a7fdc0e3e9a2448989 сохранил обе истории45 файлов и запрещает обе предыдущие session. Актуальный baseline244game/23LOCAL SHA6cd6ac15025cce3119236b1e52d998a5d850e86c95ec6eace16c1af70e9d23bf полностью перепроверен.
- Создан свежий verified backup runtime/backups/stage10_11_2-local-before-new-probe:23/23,637641bytes, manifest SHA930d18dfebd8a3c4fdb9c2460d599de33a4a2d8780c5b58a18d8da77405366c1. Payload SHA/size/mtime и источники после копирования PASS. Старые backup/quarantine/receipts сохранены. Отдельный existing closed preflight с новым планом: installed23/backup23/history45/latch UNUSED/full baseline PASS.
-27 новых целевых regression tests; полный suite885 testsRun/884PASS/1skip/0failures17.852s,exit0. Skip прежний directory-symlink privilege; права не менялись. Py_compile/diff check PASS. Public tests.json/preparation.json; private runtime/stage10_11_2/tests.log. docs/STAGE10_11_2.md содержит одну готовую PowerShell-команду, порядок Y/N/ESC и ограничения.
- Игра/сервер не запускались, live Bridge/probe/spawn/observe/destroy/rollback не выполнялись; EMF/Lua/Observer/игровые ресурсы/saves/latch/истории не изменялись. spawn_ready=false,production_spawn_ready=false,render UNKNOWN. Следующий шаг — отдельно согласованный ручной эксперимент с локальной клавишей, затем визуальная проверка и новый post-close audit. Код/тесты/отчёт публикуются в GitHub, затем остановка.

## 2026-11-18 — Stage 10.11.2: свежий closed preflight разрешённого ручного эксперимента

- Пользователь разрешил эксперимент Stage10.11.2: игру и локальный CLI запускает самостоятельно, непосредственное согласие spawn только клавишейY. Агент выполняет preflight, read-only LOCAL/context/наблюдение и post-close audit; повторы/destroy/rollback запрещены.
- Свежий preflight16:17:19–16:17:51UTC exit0: pinned local plan, installed23, backup23, обе истории45, UNUSED latch и полный актуальный baseline244game/23LOCAL PASS. Игра/сервер закрыты. READY_FOR_MANUAL_START. Evidence runtime/stage10_11_2/live/20261118T161719780155Z/preflight.json и preflight.log; public live-preflight-20261118T161719780155Z.json.
- Код не менялся, unit-тесты повторно не запускались. CLI/Bridge/prepare/spawn агентом не выполнялись, игровые файлы/saves/latch/истории не изменялись; spawn_ready=false.
- Следующий шаг: пользователь вручную загружает LOCAL Body Test / AI Body Test slot1, сообщает «загрузился». После read-only проверки нового PID/LOCAL/session/NEW предоставить готовую PowerShell-команду с локальнойY. После ручного закрытия выполнить post-close audit и опубликовать итог в GitHub.

## 2026-11-18 — Stage 10.11.2: LOCAL context PASS, команда передана пользователю

- После ручной загрузки PID249976, старт19:18:15 местного времени, выполнены read-only hello/state и continuation status. EMF0.6.18/API46/build1287369, LOCAL Body Test / AI Body Test slot1/1, player1 health100/100 PASS. Session новая относительно обеих предыдущих, controller NEW, latch UNUSED.
- Штатный CLI проверил pinned plan/install receipt/backup/обе истории. Новый probe.json, interactive-started.json и общий spawn-intent отсутствуют. Игровые prepare/spawn и локальный interactive CLI агентом не выполнялись. Private evidence runtime/stage10_11_2/live/20261118T161719780155Z/session249976; public live-context-249976.json.
- Пользователю предоставляется одна готовая PowerShell-команда для фактического PID249976. Пользователь сам запускает её, осматривает место, остаётся неподвижен, после READY/приглашения нажимает свежую английскуюY без Enter либо N/ESC. При ошибке/отмене не повторять. Никакого согласия spawn через чат нет. История/игровые файлы/saves/latch агентом не изменены, spawn_ready=false.
- Следующий шаг: результат ручного CLI и визуальное сообщение пользователя, затем разрешённое read-only наблюдение при успешном создании. После ручного закрытия — post-close audit и публикация. Код/тесты в этой проверке не менялись/не запускались повторно.

## 2026-11-18 — Stage 10.11.2: локальный CLI остановлен ground_unconfirmed

- Пользователь самостоятельно запустил local_interactive_spawn.py и прислал скриншот CONTROLLER_REFUSED:ground_unconfirmed. Проверены локальные request/response/error журналы без новых команд в игру: один probe, контроллер STOPPED/ground_unconfirmed/attempted=false. READY не достигнут, ready-window и local-confirmation отсутствуют, spawn-request0, общий spawn-intent отсутствует, latch UNUSED.
- Штатные install/backup gates повторно PASS; обе прежние истории45 файлов неизменны. Evidence compatibility/experiments/stage10_11_2/ground-refusal-249976.json и private session249976/ground-refusal.json. Игра PID249976 ещё работает. CLI отработал ошибку до локального подтверждения и spawn; механизм Y в этом live-тесте не достигнут/не подтверждён.
- ground_unconfirmed объединяет отказ ground query, недостоверные координаты, отклонение X/Z, перепад высоты более0.75m, fog и water. Точный подпункт текущий контроллер не сообщает; утверждать конкретную причину по одному коду нельзя. Safety gates не ослаблялись, установленный Lua не менялся.
- Агент не повторял probe/spawn, не менял latch/игровые файлы/saves, не выполнял destroy/rollback. Следующий шаг — пользователь закрывает игру, затем post-close audit и публикация результатов. spawn_ready=false,production_spawn_ready=false,render UNKNOWN. Тесты повторно не запускались, код не изменён.

## 2026-11-18 — Stage 10.11.2: post-close audit PID249976 и публикация итога

- Игра/сервер закрыты. Новый read-only scripts/audit_stage10_11_2_closed.py применил текущий baseline6cd6ac... и существующие install/backup/snapshot/post_close_v2 валидаторы. POST_CLOSE_INTEGRITY_PASS_SPAWN_NOT_EXECUTED; public post-close-249976.json.
- Originals67 и shadow77 точно неизменны, installed23/backup23 PASS. Только точный rename прошлого лога плюс штатные текущие логи/mtime chain_status; неизвестных изменений нет. LOCAL23 без добавлений/удалений, content7/metadata8 изменены; имена сохранены,10 world-save событий. Семантика saves не установлена, restore не выполнялся. Новый snapshot SHA283893ac38d72220b10af73e9a131d269000031de0259b263d9bef84674daf19.
- GROUND_REQUESTED19:21:16.009 → STOPPED ground_unconfirmed19:21:20.403 (4.394s). Это отказ ground guard, не timeout; точный подпункт неизвестен. Ни READY, ни local-confirmation, ни spawn-intent нет;0 spawn-request, latch UNUSED. Предыдущие45 файлов истории сохранены; текущая история также не изменялась/не удалялась. Локальное нажатиеY/создание/render этим запуском не проверены.
- docs/STAGE10_11_2_RUNTIME.md содержит результаты, ограничения и evidence paths. Реально повторены29 tests runtime_validation:29PASS/0failures/0.003s,exit0; py_compile/diff check PASS. Полный suite не повторялся. Приватные логи/binding/saves не публикуются.
- Пользователь спрашивал о другом месте: оно может подойти, но следующая попытка требует отдельного continuation plan со всеми тремя историями и новым baseline/backup; сейчас новая попытка не готовилась и не запускалась. Игровые файлы/моды/saves/latch не менялись агентом, destroy/reset/rollback не выполнялись. spawn_ready=false,production_spawn_ready=false,render UNKNOWN. Публикация отчёта/аудита и остановка.


## 2026-11-18 — Stage 10.11.3: Smart Spawn Position, офлайн-подготовка

- Подготовлен aic_first_spawn0.1.1: восемь направлений через45° на радиусе4м в диапазоне3–5м; ограниченная группа8Ground, затем последовательные Wall/Path, первая прошедшая точка. ground_unconfirmed заменён отдельными причинами; AIC_POSITION пишет requested/actualXYZ, высоту, deltaY, fog/water/API result/why. Y=0 отказавшего Ground callback явно не считается измерением.
- Точечно проверен уже имеющийся upstream fa6efdac… GroundService: очередь64/server-step, mutex, Lua callback/load binding; подтверждены overlapping pending queries, а не CPU-параллельность. Cancel API не придуман. Timeout/исключение не сбрасывают pending; новый поиск запрещён до завершения очереди. EMF/Bridge/template/shadow исследования не повторялись.
- Новый SmartPositionClient и scripts/smart_spawn_position.py разделяют --search-only/--interactive/--settle-only. Явный повтор поиска в той же сессии возможен только при UNUSED latch, отсутствии общего spawn-intent, pending0/attempted=false и закрытой hash-sealed истории. Неизвестная сессия/reload/незавершённый журнал блокируют продолжение; автоматических повторов/сброса latch/удаления истории нет.
- ЛокальнаяY/N/ESC без Enter и защита от буферизованной/удержаннойY сохранены;20s от probe, минимум8s подтверждения+2s отправки. Перед spawn повторно сверяются показанныеXYZ, context/session/nonce/deadline и прежние Lua guards. Общий fsynced intent и Lua latch по-прежнему разрешают не более одной native попытки; неопределённый исход запрещает повтор.
- Свежий closed preflight и итоговый read-only audit совпали с последним baseline283893ac38d72220b10af73e9a131d269000031de0259b263d9bef84674daf19:245game/23LOCAL. Installed23/прежний backup23 PASS, latch UNUSED. Все75 файлов трёх прошлых probes сохранены и pinned, запросов spawn/intent нет. Итог compatibility/experiments/stage10_11_3/final-integrity.json.
- Exact update manifest52a54fb2fa446df5d83527407ed3faf795739f0dae5f3dd2f66698c67a3310c9 содержит только README.md/controller.lua/main.lua/mod.json и effective23. Payload dist/stage10_11_first_spawn_0_1_1. Binding/latch/INI не обновляются. Private plan d137680beff2ccc68fedefd87617202075a1d367407ddd34096ae43537d6647c сохраняет всю историю. Подготовлен/предварительно проверен backup PLAN27files/650492bytes (LOCAL23+старые4); новая копия не создавалась.
- 62 дополнительных целевых проверки PASS. Финальный полный suite947testsRun/946PASS/1skip/0failures/0errors/18.460s,exit0. Прежний skip directory-symlink privilege; права не менялись. Проверка XYZ выявила неполный mock без координат, fixture исправлен без ослабления guard; затем полный suite прошёл. Старые0.1.0 fixtures сохранены отдельно,0.1.1 проверен новым набором Lua/Python/host/deployment tests. Py_compile/diff check PASS.
- Обновлены docs/PROTOCOL.md, TEST_PLAN.md, TEST_RESULTS.md; подробный docs/STAGE10_11_3.md содержит доказательства API, хеши, план установки/rollback dry-run и будущего эксперимента. Установка0.1.1, новый verified backup и receipt НЕ выполнены; runtime gate блокирует старый0.1.0. Игру/сервер не запускали, Bridge/probe/spawn/destroy/rollback не выполняли, игровые файлы/saves/EMF/Observer/shadow не изменяли.
- Оставшиеся ограничения: производительность8Ground/Path и окно дляY не измерены в игре; радиус4м не гарантирует безопасную точку; Wall/Path не исключают мелкую воду/динамические препятствия; render/peaceful behavior/persistence/generation ID не подтверждены. Старую точную причину ground_unconfirmed восстановить из отсутствующих полей нельзя. spawn_ready=false,production_spawn_ready=false,render UNKNOWN.
- Следующий шаг после публикации — остановка. Отдельно согласовать установку только4 файлов с verified backup27/new receipt/effective23/rollback dry-run, затем новый игровой эксперимент. Ни подготовка, ни успешные тесты не являются разрешением на установку или spawn.


## 2026-11-18 — Stage 10.11.3: разрешённая установка 0.1.1

- Пользователь отдельно разрешил backup27 и установку exact4, запретил запуск игры/spawn. Свежий closed preflight подтвердил build/Steam idle, baseline245game/23LOCAL, installed23, payload4, историю75 и UNUSED latch. Старые receipts/backup/quarantine сохранены.
- Создан verified backup runtime/backups/stage10_11_3-before-update:27/27,650492bytes, SHA manifest7d445cf14a2c7cb8158304de47de5be4d6fdb25e39583ea662d81389e155cb6c. Копия содержит LOCAL23+старые4 файла; исходные saves не изменены.
- Установлены ровно README.md/controller.lua/main.lua/mod.json aic_first_spawn0.1.1 по manifest52a54fb2…; payload не изменялся. Итог4/4 и23/23 effective hashes PASS. Прочие241game и23LOCAL полностью неизменны, состав245game сохранён; binding/latch/INI/EMF/Observer/patch/shadow не изменены.
- Новый receipt compatibility/experiments/stage10_11_3/installation/receipt.json SHA d973898fbd447f274fbf2365a9146d1b193a01413677d253fbcfbfc0da338485. Новый post-install baseline0cc0a9b1564e35d8c6b8cd586baa737b49cdbf352f86a97cf3d16df09539375e. Rollback dry-run4 PASS; rollback не выполнялся.
- Добавлен точный установщик с предварительной проверкой всех источников и эксклюзивным before/after журналом; отказ сохраняет partial state без автоматического отката.5 новых тестов PASS. Полный suite952testsRun/951PASS/1skip/0failures/0errors/22.084s,exit0; skip прежний Windows symlink privilege. Py_compile/diff check PASS.
- docs/STAGE10_11_3_INSTALLATION.md содержит отчёт, пути, SHA, готовую PowerShell-команду с получением PID уже запущенной игры и порядок следующего эксперимента. scripts/preflight_stage10_11_3.py использует новый pinned receipt/baseline, проверяет закрытые игру/сервер, установку/backup/историю.
- После установки отдельно выполнен новый closed preflight: installed23/backup27/baseline245/23/history75/UNUSED PASS. Публичная запись installation/closed-preflight.json; runtime NOT RUN.
- Игра/сервер не запускались, Bridge/probe/spawn/destroy/rollback не выполнялись, saves не изменялись. Runtime0.1.1 NOT RUN; spawn_ready=false,production_spawn_ready=false,render UNKNOWN. Следующий шаг — отдельное согласование игрового эксперимента, свежий closed preflight, ручной запуск LOCAL Body Test / AI Body Test и непосредственная локальнаяY только после READY. Публикация исходников/тестов/receipt/отчёта и остановка.


## 2026-11-18 — Stage 10.11.3: preflight разрешённого игрового эксперимента

- Пользователь разрешил игровой эксперимент с ручным запуском/закрытием игры и локальным подтверждением Y; при неудачном поиске разрешён явный ручной повтор по протоколу, без обхода pending/history/latch/intent. Автоматические попытки, destroy и rollback не разрешены.
- Свежий scripts/preflight_stage10_11_3.py выполнен, exit0: CLOSED_PREFLIGHT_PASS. Игра/сервер закрыты; installed23, backup27, post-install baseline245game/23LOCAL, история75 и UNUSED latch подтверждены. Использован pinned receipt d973898f… и baseline0cc0a9…. Имена LOCAL Body Test / AI Body Test проверены чтением slot1 descriptors. READY_FOR_MANUAL_START.
- Новая запись preflight сохранена в runtime/stage10_11_3/live и compatibility/experiments/stage10_11_3/live. Проверки исторического этапа не подменяют свежий результат. Код не менялся, unit-тесты повторно не запускались. Bridge/probe/spawn/rollback и игровые записи не выполнялись; spawn_ready=false.
- Следующий шаг: пользователь вручную загружает LOCAL Body Test / AI Body Test slot1/1 и сообщает о загрузке; затем read-only Bridge/context и готовая PowerShell-команда. Y остаётся единственным непосредственным разрешением spawn. После ручного закрытия — post-close audit, отчёт и публикация в GitHub.


## 2026-11-18 — Stage 10.11.3: загруженный мир PID257936

- После сообщения пользователя выполнены только read-only Bridge hello/state и controller status с адресным доступом к PID257936. Enshrouded запущен пользователем, StartTime19:58:22 местного времени. LOCAL Body Test / AI Body Test slot1/1, player1, health100/100; EMF0.6.18/API46/build1287369 и aic_first_spawn0.1.1 прошли validate_context.
- Installed23/backup27 повторно проверены runtime gate. Controller NEW, pending0, attempted=false, recoverable=true, latch UNUSED; прежние75 файлов истории сохранены, новые status request/response записаны отдельно в smart-control. Probe/spawn не выполнялись.
- Evidence runtime/stage10_11_3/live/20261118T165734028417Z/session257936; публичный checkpoint compatibility/experiments/stage10_11_3/live/session257936-context.json. Игровые файлы/saves/latch не изменялись агентом; код/unit-тесты не менялись/не перезапускались. spawn_ready=false, render UNKNOWN.
- Пользователю выдана готовая команда smart_spawn_position.py --interactive с PID257936, plan d137680b… и receipt d973898f…. Следующий шаг — пользователь самостоятельно запускает CLI, остаётся неподвижен, свежаяY только после READY; N/ESC отменяют. При отказе ручной новый поиск разрешён лишь по протоколу закрытой истории/UNUSED/безintent. После результата — визуальная проверка/read-only наблюдение, после ручного закрытия — аудит и публикация.


## 2026-11-18 — Stage 10.11.3: однократный spawn и визуальная проверка

- Пользователь самостоятельно выполнил local CLI, свежаяY после READY записана при остатке12.235s. Поиск000001, выбран candidate1; сохранён общий durable intent. Ответ spawn: RETURNED_UNVERIFIED, entity6959, attempted=true, pending0, recoverable=false. Зафиксирован ровно один запрос spawn; latch SPENT. Повторный поиск/spawn теперь запрещён.
- Пользователь прислал три скриншота: сначала человекоподобное тело в одежде лежит на боку, затем стоит рядом с игроком; видны маска/одежда/конечности и подсказка E «Поговорить / Изготовить». На вопрос о реакции пользователь ответил: «подощел он встал». Визуальное отображение тела подтверждено скриншотами, смена позы — сообщением пользователя и последовательностью кадров. Движение всех анимаций, диалог/крафт, мирное поведение и follow не объявляются проверенными.
- Агент выполнил только три read-only observe за30.50s (17:02:51.578–17:03:22.078UTC). Во всех entity6959/npc2939921867/faction11/player=false/animation=true/saved_state=true; позиция немного изменилась между первыми двумя снимками и совпала в последнем. Это не доказательство следования или владения instance generation.
- Read API вернул character_setup=false, render_equipment=false, force_save=false. Эти результаты конкретных template lookups не отменяют наблюдаемый render и не доказывают отсутствие визуальных ресурсов: интерпретация остаётся открытой. Само animation=true подтверждает наличие компонента, не качество анимаций. UI prompt не доказывает успешный диалог или отсутствие агрессии.
- Evidence runtime/stage10_11_3/live/20261118T165734028417Z/session257936/observation; public live/session257936-observation.json. Игровые мутации выполнял только согласованный пользовательский CLI поY; агент не выполнял spawn/destroy/rollback или запись игровых файлов/saves. Код и unit-тесты не менялись/не повторялись. spawn_ready=false,production_spawn_ready=false сохраняются.
- 30–60-секундное read-only наблюдение завершено. Следующий шаг — ручное закрытие игры пользователем, post-close audit относительно0cc0a9… с отдельной атрибуцией SPENT latch и игровых autosaves, сбор AIC_POSITION logs, отчёт и публикация. До аудита сохранение/очистка NPC не подтверждены; нового запуска или повторного spawn нет.


## 2026-11-18 — Stage 10.11.3: post-close audit PID257936 и итог эксперимента

- Пользователь закрыл игру; отсутствие Enshrouded/server подтверждено. Новый read-only scripts/audit_stage10_11_3_closed.py завершился POST_CLOSE_INTEGRITY_PASS_SINGLE_SPAWN_VISUALLY_CONFIRMED, exit0. Использован post-install baseline0cc0a9…, без старого rollback/сбросов.
- Originals67/67, shadow77/77 и immutable installed22/22 точно совпали по хешам/metadata. Latch39bytes изменён UNUSED→SPENT в том же файле/сессии; переход строго сопоставлен с localY/intent/request/result/native log. Post_close_v2 не ослаблен: отдельная атрибуция latch, исходный raw snapshot сохранён. Остальные изменения — точный rename прежнего лога, текущие логи и mtime пустого chain_status; неизвестных изменений нет. Game inventory246.
- Backup27/27 повторно verified; прежние75 файлов истории неизменны, полный journal112 файлов, отдельно observation evidence. LOCAL23 без добавлений/удалений,7 content/8 metadata changes; имена Body Test/AI Body Test сохранены,12 world-save событий. Семантика saves и сохранение самого NPC не установлены, restore/reload не выполнялись. Новый snapshot SHA120850afac7ff4242f5e07b32f8fa071607c2af411a06681cadf61e7bc56fe80.
- Логи подтвердили8 принятых/завершённых Ground, отказ candidate3 по ground_height_delta+1.50098m, Wall false и Path found/reaches/length4/count2 для candidate1. GROUND20:01:21.320→READY20:01:25.929,4.609s; после свежейY один SPAWN_ATTEMPT/ENTITY_ID_RETURNED6959 в20:01:29.441. Повтор поиска в runtime не потребовался и не проверялся; общий spawn intent и SPENT сохранены.
- Визуальное humanoid тело/одежда подтверждены скриншотами; пользователь сообщил, что при приближении NPC встал. UI «Поговорить / Изготовить» виден; диалог/крафт, мирное поведение, follow/Brain и persistence после reload не объявляются проверенными. Три observe за30.50s подтвердили согласованные ID/npc/faction и изменение позиции0.712m, но не generation identity. Неоднозначные template lookup flags отмечены в отчёте без повторного исследования/изменения payload.
- 29/29 runtime_validation tests PASS,0failures/errors/skips,0.011s,exit0; py_compile/diff check PASS. Полный suite952 этапа установки не повторялся. Контроллер/CLI/установленные моды не менялись, агент не выполнял spawn/destroy/rollback, не писал saves и не запускал игру.
- docs/STAGE10_11_3_RUNTIME.md и public post-close-257936.json содержат итог, таймлайн, все Ground/Path данные, хеши логов, ограничения и ссылки на evidence. Сырые логи, deployment key, saves/backup остаются приватными. Публикуются также ранее собранные preflight/context/observation записи. spawn_ready=false,production_spawn_ready=false; визуальный render подтверждён пользователем. После commit/push — остановка, без повторного spawn или нового запуска игры.

## 2026-11-22 — Stage 10.12: offline discovery и Companion Movement

- Подготовлен отдельный выключенный мод aic_companion_movement 0.1.0: read-only поиск по npcId2939921867, faction11 и компонентам, результаты FOUND_ONE/NOT_FOUND/AMBIGUOUS. Подсчитываются все дубликаты npcId, не только совпавшая faction. Entity6959 не используется как постоянный идентификатор. GUID ожидаемого шаблона возвращается только как профиль, guid_verified=false: getter template GUID/generation живой сущности в проверенных Lua bindings не найден. Persistence после reload и непрерывность instance identity остаются неизвестными.
- По имеющемуся source fa6efdac… подтверждены villager_move API46, штатный NpcCommandEvent GoToPosition, home/radius/leash, AI/sleep поля и ограничения callback arrived. Новых исследований Shadow Resources/template/Bridge не проводилось. Наблюдения пользователя о ночном сне/пробуждении/дневном движении отмечены отдельно от выводов из исходников.
- Подготовлен move_to prototype: одна попытка, повторная проверка текущей уникальности/session/context, отсутствие чужого заказа, цель2–5m, timeout30s/stuck10s/arrive0.5m, без hold/телепорта/pathfinding. Разделены API acceptance, неподтверждённая доставка события, наблюдаемое смещение/прогресс и близость после callback. Lua allow_move=false и выключенный mod.json сохранены; CLI предоставляет только discover/status. Для движения требуется отдельное разрешение и reviewed включение после идентификации NPC.
- Python MovementClient переиспользует pinned transport и строгий validate_context с отдельным фиксированным movement profile, не ослабляя старый spawn profile. Перед будущей командой движения пишет отдельный exclusive/fsync movement intent; при неоднозначном ответе повтор не выполняется. Старые spawn intent, SPENT и истории не изменяются. Локальная защита движения не является постоянным instance ownership и не должна обходиться новым intent path/reload.
- 22/22 новых теста PASS. Полный окончательный suite:974 tests,973 PASS,1 SKIP,0failures/errors,19.716s,exit0. SKIP уточнён отдельным verbose запуском: directory symlink,WinError1314; системные права не менялись. Проверены Lua main/controller, discovery, дубли, context/session, API отказ/исключение, таймаут, прогресс/arrival, запрет повтора и durable intent. Игровая работоспособность не заявляется.
- docs/STAGE10_12.md содержит источники, механику ремесленников, протокол и конкретный будущий ручной тест. Исторический post-close baseline120850… указан без выдачи за свежую проверку. Следующий шаг: отдельное согласование установки read-only discovery и проверка сохранённого NPC после ручной загрузки; затем отдельно движение. Игра/сервер/Bridge не запускались, ничего не устанавливалось, игровые ресурсы/saves/faction/inventory/persistence не менялись. Spawn/destroy/move/rollback не выполнялись. Код, тесты и отчёт подготовлены к commit/push; после публикации — остановка.

## 2026-11-22 — Stage 10.12: разрешённая установка read-only Discovery

- Свежий closed preflight PASS: игра/сервер закрыты, Steam build/depot прежние; полный snapshot246 game/23 LOCAL точно совпал с post-close120850… по хешам/metadata. Новая проверка, не ссылка на старый PASS.
- Создан и verified backup23 LOCAL,637831bytes в runtime/backups/stage10_12-discovery-local; manifest SHA dc2fa0d55b1f93806779299a8470e900297947bf8f0a187d192efac0a54881fe. Прежние backup/quarantine сохранены.
- Установлены только5 новых файлов aic_companion_movement0.1.0: main/controller/mod.json/README и emf/config/aic_companion_movement.ini. Config enabled=1, Lua allow_move=false. Pinned exact manifest5e0c7b…; exclusive create без overwrite/rollback. 5/5 hashes PASS; исходные246 game-файлов,23 LOCAL и112 файлов истории неизменны, SPENT/intent подтверждены. Existing Spawn Controller, observer/content, originals/shadow не менялись.
- Receipt SHA0cc3b3e3cd2db671ad3ec0e5e88d8a5bb0740a8b8b3e6e389219f47a6b10340c. Новый pre-runtime baseline251/23 SHA9efbdf467f494e57b6938c8923b139b62b9ff0c612a3dae3edd5d5948a48a90f, runtime/stage10_12/discovery-install/inventory-after.json. Public manifest/receipt и docs/STAGE10_12_DISCOVERY_RUNTIME.md подготовлены.
- 22/22 целевых теста PASS,0.023s; полный suite не повторялся. Игра/сервер/Bridge не запускались, spawn/move_to/destroy/rollback не выполнялись. READY_FOR_MANUAL_START: пользователь вручную загружает LOCAL Body Test/AI Body Test slot1/1; затем только context/discover. NOT_FOUND/AMBIGUOUS — остановка без нового NPC. После ручного закрытия — короткий аудит и публикация GitHub; runtime и persistence пока не проверены.

## 2026-11-22 — Stage 10.12: загруженный LOCAL context проверен

- Пользователь вручную запустил Enshrouded PID437520 (18:04:11) и сообщил о загрузке. Bridge hello/state через MovementClient.context подтвердили LOCAL Body Test slot1, AI Body Test slot1, player1, ожидаемые build/EMF и точный набор версий модов, включая aic_companion_movement0.1.0.
- Sandbox подключение к named pipe вернуло ACCESS_DENIED/error5; адресная read-only проверка вне sandbox через штатное согласование успешно выполнена. Права доступа/игровые настройки не менялись; ошибка не трактуется как исчерпание клиентов Bridge.
- Evidence: runtime/stage10_12/session437520/context.json. Discover ещё не выполнялся, NPC не найден/не опровергнут. Пользователю предоставляется команда discover для PID437520; движение/spawn/destroy/rollback не выполнялись. Следующий шаг — результат read-only поиска, затем ручное закрытие и post-close audit/publication.

## 2026-11-22 — Stage 10.12: пользователь выполнил discover, FOUND_ONE

- Получен вывод локального CLI пользователя: FOUND_ONE,count1,entity1025,npc2939921867,faction11,session accd7a92bb0d9f0b-1,player1. Все четыре проверяемых компонента ai/common/saved/walker присутствуют. Это USER_PASTED_LOCAL_CLI_OUTPUT; независимый повтор discover агентом не выполнялся.
- Position=(3692.313232421875,893.5,1278.689697265625); home=(3698.940673828125,893.6009521484375,1280.66357421875). ai_state13=WaitingCloseToPlayer,decision3=WantsToInteract по enum имеющегося EMF source. Значения не доказывают выполненный диалог или follow.
- После перезапуска найден один совпадающий профиль NPC; entity теперь1025 вместо исторического6959. PROFILE_ONLY,guid_verified=false: непрерывность идентичности экземпляра не доказана. Результат сохранён в runtime/stage10_12/session437520/discovery-user.json и public compatibility/experiments/stage10_12/discovery-user.json с явной provenance.
- Игровые команды агент не отправлял; движение/spawn/destroy/rollback не выполнялись. Следующий шаг — ручное закрытие игры пользователем, короткий post-close audit и публикация результатов в GitHub. spawn_ready=false.

## 2026-11-22 — Stage 10.12: закрытие PID437520, аудит и публикация

- Пользователь закрыл игру; отсутствие клиента/сервера и прежняя сборка подтверждены. Свежий post-close snapshot и audit_companion_discovery_closed.py: POST_CLOSE_INTEGRITY_PASS_PROFILE_FOUND,exit0. Originals67/67,shadow77/77,installed28/28 неизменны. Backup23/23 verified,history112/112 неизменна,SPENT и spawn-intent сохранены.
- Post_close_v2 ATTRIBUTION_PASS: точный rename прежнего лога, прежний пустой chain_status с изменённым mtime, четыре текущих лога. Других изменений игровых файлов нет. Лог подтверждает загрузку Discovery и единственную консольную команду aic_companion_movement.discover; SPAWN_ATTEMPT отсутствует.
- LOCAL23 без добавлений/удалений;8 content/9 metadata changes,14 world-save событий, имена Body Test/AI Body Test сохранены. Семантическая целостность всех save данных не установлена; восстановление не выполнялось. Новый baseline252/23 SHA90164f817c4ac2bbf1f1a48876a1aee8bb381e4ffe91844ede392c0281585d32, runtime/stage10_12/session437520/post-close/inventory.json.
- Итог runtime: FOUND_ONE из пользовательского CLI,entity1025,npc2939921867,faction11,home/position/AI/components собраны; профиль обнаружен после reload, GUID/generation не доказаны. Movement/spawn/destroy/rollback не выполнялись, allow_move=false,spawn_ready=false.
- docs/STAGE10_12_DISCOVERY_RUNTIME.md и public post-close.json обновлены; к публикации также готовятся install manifest/receipt, пользовательское discovery evidence и скрипты установки/аудита. Сырые логи/backup/saves/deployment key не публикуются. Целевые22 теста прошли на установке; полный suite без необходимости не повторяли. После commit/push — остановка. Следующий этап движения только по отдельному разрешению.

## 2026-11-22 — Stage 10.12: подготовка одного ручного move_to, без установки

- Подготовлено обновление существующего aic_companion_movement0.1.0→0.1.1: четыре файла main/controller/mod.json/README. allow_move=true только в подготовленном payload; автодвижения при загрузке нет. Существующая установка0.1.0 повторно проверена5/5, SPENT и112 файлов истории/spawn-intent неизменны. Игра/сервер не запускались, Bridge не подключался, установка/движение/spawn/destroy/rollback не выполнялись.
- CLI move_to берёт цель из свежей позиции игрока на выбранной им свободной земле2–5m от NPC, проверяет FOUND_ONE/контекст/отсутствие заказа, показывает координаты и требует MOVE+Enter в течение30s. После подтверждения повторяет поиск того же session/entity/player, создаёт отдельный fixed exclusive/fsync movement-intent, отправляет один заказ и только наблюдает status. Старый entity1025 и прежние координаты не используются как цель/идентификатор.
- Lua повторно проверяет уникальность, session/context, active order, расстояние2–5m, высоту<=1m, awake state и find_wall. Радиус home/leash и навигация остаются у EMF; home/faction/inventory/persistence не меняются. Дневное время и свободная твёрдая земля без воды — явная проверка пользователя; Ground API не имитируется, проходимость заранее не гарантируется. No retry/cancel/follow/teleport; timeout/stuck EMF могут сами послать stop-position event, что описано в плане.
- Exact-update manifest SHAa4c574d4e0678caec35d1a4567ca2cdeed2a5955983a00eae1a3e099b100681d, public compatibility/experiments/stage10_12/movement-preparation/exact-update-manifest.json; локальный payload dist/stage10_12_movement_0_1_1. Перед будущей разрешённой установкой нужны fresh closed preflight и backup LOCAL+четырёх заменяемых файлов; сейчас backup не создавался. Baseline остаётся post-close90164f….
- 30/30 movement tests PASS,0.035s;66/66 Stage10.11 regressions PASS,0.250s. CLI --help без подключения PASS. Полный suite не повторяли. Новые тесты охватывают ручное подтверждение/отмену/просрочку, новый entity, active order, wall/height/sleep, version gate, один native вызов и запрет повтора. Движение в игре ещё не проверено.
- docs/STAGE10_12_MOVEMENT_TEST.md содержит готовую PowerShell-команду, границы проверок и порядок будущего теста; source/profile version0.1.1 подготовлены к commit/push. Следующий шаг — отдельное разрешение установки и затем ручного игрового теста. После публикации остановка, spawn_ready=false.

## 2026-11-22 — Stage 10.12: разрешённая установка Movement0.1.1

- Fresh closed preflight PASS: игра/сервер закрыты, Steam build/depot прежние;252 game/23 LOCAL полностью совпали с post-close90164f… по SHA/metadata. Проверены pinned manifesta4c574…,payload4,current install5, SPENT и отсутствие нового movement-intent.
- Новый verified backup27 (LOCAL23+четыре заменяемых файла),644218bytes, runtime/backups/stage10_12-movement-0_1_1; manifest SHAcc0c0101c410e35de7971330530ec7cd9433eb09f2b29529f06bfffe09ac0441. Старые backup/quarantine сохранены.
- Установлены ровно4 подготовленных файла0.1.1,4/4 хешей PASS. Остальные248 game-файлов,23 LOCAL записи и112 файлов истории неизменны, SPENT/spawn-intent сохранены; config,Spawn Controller,observer/content,originals/shadow не менялись. Новый receipt в compatibility/experiments/stage10_12/movement-installation/receipt.json.
- Новый pre-runtime baseline runtime/stage10_12/movement-installation/inventory-after.json SHAa806a328acfea8c361a4e1df5750fb08bc4599dd62d09f2a5c49eed7e3e2018d. Игра/Bridge не запускались, движение/spawn/destroy/rollback не выполнялись. Payload после30+66 прошедших тестов не менялся; full suite не повторяли, скрипт установки py_compile PASS.
- INSTALLED_READY_FOR_MANUAL_START. Пользователь вручную загружает LOCAL Body Test/AI Body Test slot1/1 и сообщает «загрузился»; после context check — один move_to с непосредственным MOVE в локальном CLI. Команда приведена в docs/STAGE10_12_MOVEMENT_TEST.md. До context check не запускать. После ручного закрытия — короткий аудит и публикация runtime результата. spawn_ready=false.

## 2026-11-22 — Stage 10.12: контекст перед ручным движением PID450416

- Пользователь вручную загрузил игру PID450416,start18:27:12. Адресный read-only Bridge hello/state вне sandbox через штатное согласование: context PASS, LOCAL Body Test/AI Body Test slot1/1,player1,ожидаемые build/EMF и версии модов, включая Movement0.1.1. Evidence runtime/stage10_12/session450416/context.json.
- Агент move_to не отправлял. Пользователю разрешается запустить локальный CLI для свежего discover, выбрать дневную свободную точку своей позицией2–5m от NPC и непосредственно подтвердить один заказ вводом MOVE. При отказе/неоднозначном результате — остановка без повторов; после ручного закрытия — аудит. Spawn/destroy/rollback не выполнялись.

## 2026-11-22 — Stage 10.12: исправление радиуса на20m по запросу пользователя

- Read-only лог PID450416 подтвердил три discover и один move_to18:30:15 с отказом TARGET_DISTANCE_2_TO_5 до native villager_move. NPC ушёл:4.577m при выборе цели→9.301m при повторном discover. Durable movement-intent существует; не удалялся и не сбрасывался. Игра остаётся запущена, post-close audit ещё не выполнен.
- Подготовлена0.1.2: Python/Lua разрешают расстояние<=20m без нижней границы. Остальные gates, home/leash EMF, ручное MOVE и запрет повторов сохранены. Это один заказ к позиции игрока, не follow. CLI требует0.1.2; старая установка0.1.1 не изменена. Новый intent/повторная попытка не создавались.
- Трёхфайловый payload controller/mod.json/README и exact manifest подготовлены в dist/stage10_12_movement_0_1_2 и compatibility/experiments/stage10_12/movement-20m. Baseline для установки ожидает закрытия игры и аудита. 32/32 целевых теста PASS,0.051s; проверены1m/9.3m/20m и отказ>20m. Никаких установок/игровых мутаций агент не выполнял.
- Обновлён docs/STAGE10_12_MOVEMENT_TEST.md; код и результаты подготовки публикуются в GitHub. Следующий шаг — пользователь закрывает игру, затем post-close audit и подготовка установки/новой попытки с сохранением всей истории. На текущем intent повторная команда остаётся заблокированной.

## 2026-11-22 — Stage 10.12: post-close450416, установка0.1.2 и отдельная попытка20m

- Пользователь закрыл игру в рамках согласованного перехода. Closed audit PASS: originals67/shadow77/installed28 неизменны,backup27 verified,history112/SPENT сохранены. LOCAL23:8 content/9 metadata changes,17 world saves,без добавлений/удалений. Логи атрибутированы post_close_v2. Единственный move_to сопоставлен с прежним intent и отказом TARGET_DISTANCE_2_TO_5 по nonce/session/entity/target/approval; installed controller подтверждает assert до native API. Итог POST_CLOSE_PASS_MOVE_REFUSED_BEFORE_NATIVE. Старый intent SHA3a95622cca0de46bb0edf29b46b18810cb63e490737bd7d1f696918e49309d33 сохранён.
- Fresh preflight по post-close5a611d… PASS. Создан verified backup26 (LOCAL23+3 старых файла),643580bytes; manifest SHAce2158275bedad8c6213714aa796b3905c86104b842ffb65fbf1bcc9d9b55499. Установлены только controller/mod.json/README0.1.2 по manifest18663c…,3/3 hashes PASS. Остальные250 game-файлов,23 LOCAL и112 историй неизменны; старый movement-intent повторно сверён. Main/config,Spawn Controller,SPENT,spawn-intent,observer/content не менялись.
- Новый pre-runtime baseline runtime/stage10_12/movement-20m-installation/inventory-after.json SHA25eb067ef2f33f2a017f42f26341bc4a5e07bf99bb098a81a96bbfcd26c08fd8. Receipt public compatibility/experiments/stage10_12/movement-20m-installation/receipt.json.
- CLI использует отдельный каталог movement-20m-attempt только после pinned audit f801a6… и совпадения старого intent. Прежняя история не сбрасывается; новый intent ещё не создан, возникнет только при локальном MOVE. 34/34 целевых теста PASS,0.064s; full suite не повторяли. Никакого автоматического retry/движения/запуска игры/destroy/rollback не было.
- READY_FOR_MANUAL_START: вручную LOCAL Body Test/AI Body Test slot1/1, затем context check и одна локальная команда в пределах20m. Документация, audit/receipt и код публикуются в GitHub. Следующий шаг — сообщение пользователя «загрузился»; spawn_ready=false.
- 2026-11-22 — Runtime context Movement 0.1.2, PID456828: свежая read-only проверка Bridge hello/state и строгого контекста PASS; LOCAL Body Test slot1 / AI Body Test slot1, player1. Evidence: runtime/stage10_12/session456828/context.json. Проверены pinned audit предыдущего отказа и сохранённый intent; новый movement-20m-attempt/movement-intent.json отсутствует. Команды движения не выполнялись; пользователю выдана команда локального CLI с непосредственным MOVE+Enter для одной попытки в пределах20m. Следующий шаг — результат ручной команды, затем после закрытия игры короткий аудит. Реальное движение ещё не подтверждено; spawn_ready=false.

## 2026-11-22 — Movement 0.1.2: наблюдение после ручного MOVE
- Пользователь сообщил «подошел» и предоставил вывод локального CLI. Проверен runtime/stage10_12/movement-20m-attempt/result.json: order1 ACCEPTED, 16 отсчётов, расстояние от цели уменьшилось с 2.175595 до минимума 0.699490 м; displacement_observed/progress_observed=true. Итог STUCK, engine_result=stuck, финальное расстояние1.096443 м. Подход визуально подтверждён пользователем; успешное завершение штатного заказа не подтверждено. Причина STUCK пока не установлена; event_sent остаётся UNVERIFIED, идентичность PROFILE_ONLY.
- Прочитаны существующие результаты; новых игровых команд, повторов или изменений установленного кода не выполняли. История и durable intent сохранены. Тесты не повторяли: код не изменён. Следующий шаг — ручное закрытие игры, короткий post-close audit и публикация итогов в GitHub. Spawn_ready=false.

## 2026-11-22 — Movement 0.1.2: post-close PID456828 завершён
- Пользователь подтвердил закрытие игры и предположил, что NPC упирался в его персонажа. Цель совпадала с позицией игрока, arrive=0.5; минимум0.699490м. Столкновение — согласующаяся с наблюдениями гипотеза, не установленная причина STUCK. Подход наблюдался; успешное завершение заказа не подтверждено.
- Свежий closed/build audit PASS: оригиналы67, shadow77, установленные28 неизменны; backup26/26 проверен;112 записей истории/SPENT и старый intent сохранены. В EMF ровно1 move_to,2 discover,16 status. LOCAL23 без добавлений/удалений,8 content/9 metadata изменений,15 world-save events; имена сохранены, семантическая целостность не установлена. Post_close_v2 ATTRIBUTION_PASS.
- Новый baseline runtime/stage10_12/session456828/post-close/inventory.json SHA9698e1e8e0437b22bc4bbfca40e065379bc7001343343b438aff2ca8d858e553. Вердикт POST_CLOSE_INTEGRITY_PASS_MOVEMENT_OBSERVED_ORDER_STUCK. Подробности docs/STAGE10_12_MOVEMENT_RUNTIME.md и public post-close-456828.json; сырые логи/сохранения остаются локальными.
- Аудит выполнен scripts/audit_movement_20m_closed.py, exit0. Полный suite не повторяли; игровой payload не менялся. Новых мутаций, retry, установки или rollback нет. Следующий предлагаемый шаг — подготовка незанятой точки рядом с игроком для отдельного разрешённого теста; сейчас остановка, spawn_ready=false. Отчёт и аудит подготовлены к commit/push.

## 2026-11-22 — Stage 10.13: офлайн Follow Controller и Autonomous Test Runner
- Подготовлен Movement0.2.0: новый follow.lua, follow_config.lua, интеграция main.lua; прежний discovery/controller переиспользован, legacy move_to в новой версии заблокирован. Python FollowClient/Runner работает через существующий Bridge/LOCAL validator, без ручного MOVE. Сейчас ничего не установлено и не запущено.
- Сессия180с, один заказ одновременно, максимум24 заказа/30 probes/2 recovery, cooldown4с; радиус19/20м, комфортная дистанция2м с возобновлением от2.8м. Цель1.8м рядом с игроком; Ground/Wall/Path и повторная проверка актуальности. Не больше одного незавершённого Ground/Path запроса, поздние callback не выдают движение. При выходе за20м отменяется только свой заказ; чужие заказы/неопределённость/потеря контекста останавливают управление.
- Один фиксированный durable test-session.jsonl с fsync перед командами; отдельный Lua follow-session.lock потребляется до движения и переживает reload. Старые intent/SPENT не сбрасываются. Watchdog4с; order12с/stuck6с; опциональный hold5с. Повтор команды или cancel после неизвестного результата запрещён.
- Ограниченное исследование существующих исходников подтвердило native hold/cancel и ограничения home/leash. Полное отключение roaming с сохранением villager_move не подтверждено: roamingRange=0 запрещает move. Пакет оставляет native; переключатель hold подготовлен, но это возвращение к точке после arrival, а не выключение AI. NPC в WAITING пока может гулять сам; неподвижность не обещается. Источники и ограничения в docs/STAGE10_13.md.
- Целевые69/69 PASS. Финальный suite1021:1020 PASS,1 SKIP,20.823с, Python exit0 (runtime/stage10_13-offline-tests-final.txt). Тесты включают host/reload/SPENT, отказ отмены без retry, stale callbacks/очередь, context/duplicates, recovery и budgets. Игровой follow не испытывался.
- Пакет dist/stage10_13_movement_0_2_0: ровно6 файлов (3 замены main/mod.json/README;3 новых follow.lua/follow_config.lua/follow-session.lock),31 effective hashes. Manifest SHA5e18844a7999679f1cd0af12fbf49ce00813c023b0bbc3674c90b40dab09b4c8. Будущий backup26=LOCAL23+3 заменяемых; сейчас только план, backup не создавался. Подготовка использует актуальный post-close baseline9698e1…; перед установкой нужен fresh preflight.
- Свежая read-only проверка: игра/сервер закрыты, build PASS; установленное28 неизменно, LOCAL23 неизменно,112 записей истории/старые movement intent сохранены, package6/6 hashes PASS. EMF/observer/patch/установленный Spawn Controller не изменены. Никаких live Bridge-команд, spawn/destroy/teleport/rollback или записи сохранений.
- Вердикт OFFLINE_FOLLOW_PROTOTYPE_READY_WITH_ROAMING_LIMITATION. Подготовлены код, тесты, exact manifest и отчёт для commit/push. Следующий шаг — отдельное разрешение установки, затем согласованная автоматическая сессия после «загрузился»; остановка до разрешения. Spawn_ready=false.

## 2026-11-22 — Stage 10.13: Movement0.2.0 установлен, ожидание ручного запуска
- Получено разрешение установки exact6 и одной автоматической тестовой сессии после «загрузился», без дополнительных MOVE/подтверждений. Сейчас выполнена только установка; игру/сервер Codex не запускал, Bridge/движение не вызывал.
- Свежий closed/build/payload/baseline preflight PASS. Установщик scripts/install_companion_follow.py использует существующие snapshot/verified_backup/no-links проверки, журналирует каждую операцию; новые файлы добавляет без перезаписи существующих, при ошибке останавливается без rollback. Два целевых теста установщика PASS,0.054с; полный suite повторно не запускали.
- Создан verified backup26 (LOCAL23+3 заменяемых),641142bytes: runtime/backups/stage10_13-movement_0_2_0. Manifest SHA4c287e1a4c82b969a542fa9fb90ec49c429a2319d62c635a9d897f6b37e48011;26/26 PASS.
- По неизменному exact manifest5e18844a… заменены main.lua/mod.json/README.md и добавлены follow.lua/follow_config.lua/follow-session.lock. Только6 разрешённых файлов. Installed6/6 и effective31/31 hashes PASS. Остальные251 игровых файлов (включая оригиналы и shadow),LOCAL23 и112 исторических записей неизменны; предыдущие movement intent/result сохранены, старый latch SPENT. Новый follow latch UNUSED, runtime/stage10_13/test-session.jsonl отсутствует. Roaming=native.
- Receipt runtime/stage10_13/installation/receipt.json и public compatibility/experiments/stage10_13/installation/receipt.json. Новый pre-runtime baseline runtime/stage10_13/installation/inventory-after.json SHA2a55ebc2f3f2851955f7eb85cbef3016c9ed9884d1ecdd091a23cd02e470d463. Read-only rollback dry-run PASS, никаких восстановлений/удалений не выполняли. Runner preflight PASS; реальное follow пока не проверено.
- INSTALLED_READY_FOR_MANUAL_START. Пользователь запускает LOCAL Body Test / AI Body Test slot1/1 и пишет «загрузился». Затем проверить PID/LOCAL/Bridge и запустить одну разрешённую сессию с лимитом180с,24 orders/30 probes/2 recovery; сохранять native и не запрашивать MOVE. После «закрыл» — короткий аудит и публикация итогов. До сообщения остановка; spawn_ready=false.

## 2026-11-22 — Stage 10.13 runtime PID471028: BLOCKED_COMMAND_NAME_LIMIT
- После «загрузился» проверены PID471028, Bridge hello/state, LOCAL Body Test / AI Body Test slot1/1, installed31/31 и прежние intent/history. PASS; context evidence runtime/stage10_13/session471028/context.json.
- Одна разрешённая попытка Runner остановилась на follow_start с OUTCOME_UNKNOWN_NO_RETRY. Read-only журнал EMF установил точную причину: имена aic_companion_movement.follow_start/step/stop/status имеют35/34/34/36 символов, лимит регистрации32 с учётом префикса. Все четыре обработчика отклонены при загрузке; follow_start вернул unknown command. Это ошибка подготовки интерфейса: тестовый mock регистрации не моделировал ограничение длины.
- Follow-сессия не началась: AIC_FOLLOW START/MOVE_INTENT отсутствуют, follow-session.lock остаётся UNUSED. Python test-session.jsonl создан и сохранён, повтор/сброс не выполнялись. Штатное блуждание NPC не считать работой Follow. Файл runtime/stage10_13/session471028/blocked.json и копия лога emf_core-at-failure.log сохранены.
- Установленные моды во время игры не менялись, новых NPC/команд движения/destroy/rollback не было. Следующий шаг — ручное закрытие игры, короткий post-close audit и публикация; затем исправление коротких имён команд и теста регистрации отдельным обновлением. Сейчас остановка; post-close audit ещё не выполнен, spawn_ready=false.

## 2026-11-22 — Stage10.13: post-close PID471028 завершён
- Пользователь закрыл игру. Свежий closed/build audit scripts/audit_follow_registration_closed.py завершился exit0: POST_CLOSE_INTEGRITY_PASS_FOLLOW_NOT_STARTED, runtime BLOCKED_COMMAND_NAME_LIMIT. Оригиналы67, shadow77, installed31 неизменны; backup26/26 PASS, история112/старые intent/SPENT сохранены, follow latch UNUSED. Журнал попытки не менялся (SHA9c394226b46a4698058c549a2310ab17b7a892d5c41e5256488e50a01fcc76d4).
- LOCAL23: без добавлений/удалений,6 content/7 metadata изменений; в EMF5 сохранений мира, имена Body Test/AI Body Test сохранены. Семантическая целостность не установлена, восстановления не выполняли. Изменения вне LOCAL ограничены четырьмя логами, архивом прежнего лога и mtime chain_status; post_close_v2 ATTRIBUTION_PASS.
- Журнал содержит только discover и отклонённый follow_start. Подтверждены отказы регистрации всех четырёх имён длиной35/34/34/36 при лимите32; START/MOVE_INTENT отсутствуют. Follow не начался, команды движения0, никаких retry/новых intent/сбросов/rollback. Причина — дефект интерфейса и неполный mock регистрации, не навигация NPC.
- Новый baseline runtime/stage10_13/session471028/post-close/inventory.json SHAac979a13426a5d311bd37f48e502239db238e322980249b1c8f16a2eb8629534. Public compatibility/experiments/stage10_13/post-close-471028.json; docs/STAGE10_13.md актуализирован. Raw logs/сохранения остаются локальными. Код мода/установка не менялись, полный suite не повторяли.
- Отчёт/скрипт аудита публикуются в GitHub. Предлагаемая следующая итерация: короткие имена, проверка регистрации и regression-тест32символа; затем проверяемое продолжение без удаления истории. Сейчас остановка, все сценарии Follow NOT_TESTED, spawn_ready=false.

## 2026-11-22 — Stage10.13: регистрация исправлена, Movement0.2.1 установлен
- По разрешению пользователя заменены Follow endpoint names на f_start/f_step/f_stop/f_status; полные имена29/28/28/30 символов. Python/Lua согласованы, Lua проверяет длину и возвращаемый результат emf.command, отказ регистрации завершает загрузку ошибкой. Mock регистрации теперь отвергает длинные имена; regression загружает реальный main.lua и сравнивает фактический набор команд с Python.
- Безопасное продолжение привязано к pinned audit0f6e5855…: прежний Follow не начался, движение0, lock UNUSED. Старый test-session.jsonl SHA9c394226… остаётся тем же файлом. При будущем запуске Runner захватит файловую блокировку, проверит старые байты и допишет AUDITED_CONTINUATION перед SESSION_INTENT; до запуска ничего не дописано. После первой дописи повтор блокируется hash-проверкой. Новый journal/новый lock/token для обхода не создаются; старые intent/SPENT не сбрасываются.
- Целевые71/71 теста PASS,0.160с: регистрация/реальные полные имена, старое имя отклоняется, версия/LOCAL, сохранение префикса журнала и single-use append. Дополнительно проверены exact3 и исключение follow lock из замен. Полный suite не повторяли; алгоритм Follow/лимиты/native не менялись.
- Свежий closed/build/baseline preflight PASS. Verified backup26 (LOCAL23+3 заменяемых),644217bytes: runtime/backups/stage10_13-movement_0_2_1, manifest SHAea332f1eec7f88f7bb60d49055607126f8fdca040845bbeefcacfdbeec4aff00. Установлены только main.lua/mod.json/README.md по exact manifest500d8b6bf9b73cb449d80b444f9b0d59d02e379178cc3aec04823f84c04ed918. Package dist/stage10_13_movement_0_2_1; public plan compatibility/experiments/stage10_13/registration-fix/exact-update-manifest.json.
- Installed3/3/effective31/31 PASS; остальные255 game-файлов,LOCAL23,112 историй и прежние intent/journal неизменны. Follow lock UNUSED, старый SPENT сохранён. Receipt runtime/stage10_13/registration-fix-installation/receipt.json и public registration-fix/installation/receipt.json. Новый baseline inventory-after.json SHAa67f92b091f533c807d43d6b2b984b389dcd67ecdabbb377d1992d2ce6b3a175. Runner preflight/rollback dry-run PASS; восстановлений/удалений не было.
- INSTALLED_READY_FOR_MANUAL_START. Игра/сервер не запускались, Bridge/движение не выполнялись. После «загрузился» проверить PID/LOCAL и запустить scripts/companion_follow.py --pid PID --manifest-sha256 500d8b6bf9b73cb449d80b444f9b0d59d02e379178cc3aec04823f84c04ed918 --authorized-session. Одно продолжение уже разрешено, MOVE/новых подтверждений не требуется. После «закрыл» аудит; сравнивать прежний журнал как сохранённый префикс после разрешённой дописи. До сообщения остановка. Spawn_ready=false.

### 2026-11-22 — Stage10.13: runtime Movement0.2.1, PID471612

- После «загрузился» проверены Bridge и LOCAL Body Test / AI Body Test slot1/1, effective31, прежние intent/history и reviewed continuation. Запущена ровно одна разрешённая Follow-сессия; новых подтверждений не запрашивали.
- Регистрация коротких команд работает: AIC_FOLLOW START 19:42:11.705; NPC1025, PROFILE_ONLY, native roaming. Собрано30 samples,5 probes; команд движения0, восстановлений0. Фактическое следование не подтверждено; пользователь сообщил «не ходит за мной».
- Первые проверки теряли актуальность (PROBE_POSITION_CHANGED). В19:42:47.858 контроллер остановился GROUND_REFUSED: Ground API ok=true, fog=none, y=893.5009765625; NPC origin y=894.98779296875, перепад1.48681640625м превышает установленный предел1м. Это достаточное условие отказа в follow.lua:75, а не отказ самого Ground API. Следующий f_step получил SESSION_STOPPED; автоматических повторов нет. Повторный обработчик записал REQUEST_ERROR; summary.stopped_reason содержит устаревший PROBE_POSITION_CHANGED, окончательную причину устанавливает core log.
- Исходные4 строки test-session.jsonl сохранены побайтно (SHA9c394226…); разрешённое продолжение дописано в тот же файл. Новый journal SHA5e9b66266c46d6f7682319890c894aeacde710cd045604dd7591933429283b03. Follow lock закономерно SPENT!, не сбрасывался. Снимок core log и runtime-result.json сохранены в runtime/stage10_13/session471612. Spawn/destroy/ручных игровых изменений не выполняли.
- Игра ещё не подтверждена закрытой. Post-close audit и публикация результатов в GitHub ожидают «закрыл». Установленные моды не исправлялись на ходу. Следующий шаг: закрытие пользователем и короткий аудит; повтор Follow не запускать. Spawn_ready=false.

### 2026-11-22 — Stage10.13: post-close PID471612 завершён

- После «закрыл» выполнен scripts/audit_follow_runtime_closed.py, exit0: POST_CLOSE_INTEGRITY_PASS_FOLLOW_STOPPED. Игра/сервер закрыты, build/depot прежние. Оригиналы67/67, shadow77/77 и30 неизменяемых installed-файлов без изменений; 31-й Follow lock содержит ожидаемый SPENT!. Backup26/26, история112, старые intent/SPENT и исходный префикс Follow-журнала проверены.
- LOCAL23, добавлений/удалений0, content8/metadata9 изменений;12 world-save событий. Body Test / AI Body Test сохранены, пустых/связанных файлов нет. Семантическая целостность сохранений не доказана; никаких восстановлений или прямых изменений не выполняли. Остальные игровые изменения атрибутированы post_close_v2 как журналы/архив/chain mtime; Follow lock проверен отдельно.
- Публичный отчёт compatibility/experiments/stage10_13/post-close-471612.json; объяснение docs/STAGE10_13_FOLLOW_RUNTIME.md. Новый локальный baseline inventory SHA5bd9a38b88ce73de91bbd600af4ea7ee0baa5839a23487725be0ea43a48fc31e. Команды реально зарегистрированы: f_start30, f_step29, f_stop29, f_status31 символ вместе с префиксом (уточнение прежнего подсчёта).
- Итог игры: регистрация исправлена, Follow остановился GROUND_REFUSED до первого движения;5 probes,30 samples,0 orders. Сессия израсходована, повтор не выполнялся и прежнюю команду запускать нельзя. Документированы устаревший summary.stopped_reason и вторичный REQUEST_ERROR; код Follow/установленные файлы не менялись. Полный suite не повторяли: выполнен необходимый фактический read-only аудит. Следующий шаг — отдельная доработка Follow по полученным данным, без сброса истории. Spawn_ready=false.

### 2026-11-22 — Stage10.14: офлайн Follow0.3.0

- Уточнение принято и реализовано в исходниках: цель — самостоятельное приближение, не повтор траектории. Убраны veto по высоте0.75/1м и прямой стене;8 кандидатов, bounded retry для неподходящих Ground/Path/явного отказа move. Проверки не обнуляются только от движения игрока/NPC; перенацеливание после >8м/8с. Idle2м/resume2.8м в3D, горизонтальный предел75/80м. Native jumps с max_jump_up/down=0 допустимы в Path; собственных прыжков/глайдера нет.
- Проверены имеющиеся исходники EMF: path_find умеет jump-up/down/across, но исполнение villager_move зависит от AI. Home/roaming circle/3D leash остаются реальным ограничением. Этаж по Ground XZ и способность NPC прыгать неизвестны. Отказ по потенциальному урону не добавлен.
- Сохранены durable latch/journal, single-use, context/identity, watchdog,30 probes/24 orders/2 recoveries. Native orders30с/stuck8с. Отказ отдельной точки не завершает сессию; неизвестный исход завершает. Исправлена потеря terminal reason. Добавлены PROGRESS и расстояния до игрока в ORDER_RESULT.
- Целевые83/83 теста PASS0.227с: Follow/Movement/installation. Новые случаи ±20м, jump-down, обход100м, движущиеся игрок/NPC, альтернативы/бюджет, busy, stop reason. Полный suite не повторялся. docs/STAGE10_14.md содержит source links, ограничения и план теста; README обновлён.
- Ничего не установлено, игра/сервер не запускались, игровых команд/изменений сохранений не было. В игре0.2.1 со SPENT!, история не сбрасывалась. Reviewed update manifest и безопасное продолжение израсходованной сессии нужны отдельно; старую команду не запускать. Устойчивый Follow в игре НЕ подтверждён. Spawn_ready=false.

### 2026-11-22 — Stage10.14: пороги20/50м и готовый пакет к отдельной установке

- Follow активируется при XZ<=20м и выключается только XZ>50м; между порогами сохраняет состояние. Проверен цикл30→20→35→49→50→50.01→35→20. Дистанция прибытия остаётся3D; перепады±10/20м допустимы. Текущая позиция читается каждым step (~1с); существенное смещение обновляет цель с подтверждённой отменой только собственного приказа, без одновременных движений.
- Подготовлен exact manifest SHA0fb0bc5e73c00d504915a474dac10880b41e203495098357fd0f911135447320, compatibility/experiments/stage10_14/exact-update-manifest.json. Локальный пакет dist/stage10_14_movement_0_3_0:5 замен (main.lua/follow.lua/follow_config.lua/mod.json/README.md),1 добавление follow-stage10-14.lock. Effective32. Новый backup при разрешённой установке: LOCAL23+5=28; сейчас не создавался.
- Отдельная новая явно разрешаемая сессия Stage10.14: фиксированный token, новый lock и create-new runtime/stage10_14/test-session.jsonl. Старый follow-session.lock остаётся SPENT!, история Stage10.13/результаты/intent включены в SHA-проверки. Нет сброса, удаления, переименования или повторного использования старой сессии. Lua reload/повтор Runner не открывают новую попытку.
- Подготовлены prepare_follow_stage14.py, install_follow_stage14.py (по умолчанию read-only; запись только с отдельным разрешением и --install-approved), follow_stage14.py (receipt/effective32/история/LOCAL/version, только --authorized-session). После установки и «загрузился» одна автоматическая180с сессия без MOVE; после «закрыл» короткий аудит. Сейчас установки/запуска/движения не было.
- 90/90 целевых тестов PASS0.287с: пороги, текущая цель/single order, высоты, старые lock, manifest/source compatibility, отказ без runtime-разрешения. Полный suite не повторялся. Closed read-only preflight PASS: полные game/LOCAL snapshots совпали с post-close baseline5bd9a38b…. После правки README повторены exact6/pinned manifest/closed/build/preserved checks, PASS. Подготовлены receipt/backup/rollback dry-run механизмы, но они не исполнялись.
- docs/STAGE10_14.md и README актуализированы. Ограничение native home/leash остаётся; реальный Follow0.3.0 пока не проверен. Следующий шаг — разрешённая установка подготовленного пакета, затем отдельно разрешённое испытание. Spawn_ready=false.

### 2026-11-22 — Stage10.14: Movement0.3.0 установлен, ожидание ручного запуска

- По явному разрешению выполнен scripts/install_follow_stage14.py --install-approved, exit0. Свежие closed/build/depot/Steam idle, pinned baseline, exact payload и конфликты проверены. Verified backup28 (LOCAL23+5),654261bytes, runtime/backups/stage10_14-movement_0_3_0; SHA manifest9520210b034f5ee0c86aa2a7b47359002edce84fa31145d905c4fbc1aed95e5e.
- Выполнены ровно5 замен и1 добавление по manifest0fb0bc5e73c00d504915a474dac10880b41e203495098357fd0f911135447320. Installed6/effective32 PASS; остальные254 игровых файла иLOCAL23 совпадают с baseline. Прежние112 файлов spawn history, SPENT, Stage10.13 lock/intent/журналы/результаты сохранены. Новый follow-stage10-14.lock UNUSED; новый журнал сессии пока не создан.
- Receipt runtime/stage10_14/installation/receipt.json и compatibility/experiments/stage10_14/installation/receipt.json. Новый inventory-after.json SHA77f889dadb0261adf0f799e64df0544b99701569a246caeccb483a880280f16e. Runner preflight PASS, rollback dry-run PASS; откат не выполнялся. Подготовительные90 тестов исторические, повторно без изменений кода не запускались.
- INSTALLED_READY_FOR_MANUAL_START. Игру/сервер не запускали, Bridge/движение/spawn/destroy не вызывали, сохранения напрямую не меняли. Пользователь уже разрешил одну180с сессию Stage10.14; только после «загрузился» проверить PID/LOCAL/Bridge/version и выполнить scripts/follow_stage14.py --pid PID --manifest-sha256 0fb0bc5e73c00d504915a474dac10880b41e203495098357fd0f911135447320 --authorized-session. Дополнительный MOVE/подтверждения не нужны. После «закрыл» короткий аудит и GitHub. Spawn_ready=false.

### 2026-11-22 — Stage10.14: ночная сессия PID490800 остановлена перед дневным повтором

- После «загрузился» проверены effective32, предыдущая история, Bridge/version0.3.0 и LOCAL Body Test / AI Body Test slot1/1. PID490800 (ручной запуск20:24:02), session7ced7aa64498bde8-1, один NPC1025. Запущена ровно одна разрешённая сессия scripts/follow_stage14.py; START20:25:29.467.
- NPC оставался ai_state8/decision5, WAITING_FOR_NPC/NPC_ASLEEP_OR_BUSY. Пользователь подтвердил ночь и предложил дождаться дня и повторить. По этой просьбе выполнен штатный f_stop, подтверждён STOPPED/RUNNER_STOP; Runner завершился exit0.66 samples,0 probes,0 orders,0 recoveries; дистанция4.8905–8.5271м менялась при движении игрока. Реальное Follow/пороги/вертикальные маршруты не испытаны, успешного движения нет.
- Runtime-result.json и снимок emf_core-runtime.log сохранены в runtime/stage10_14/session490800; основной журнал сохранён на прежнем месте. Новый одноразовый lock израсходован; сброса, повторной попытки, изменения установленных файлов/сохранений нет. Post-close audit ожидает «закрыл». Пользователь хочет дневной повтор: после закрытия подготовить отдельную попытку с сохранением этой истории, не использовать старую команду повторно. Игра самостоятельно не закрывалась. Spawn_ready=false.

### 2026-11-22 — Stage10.14: post-close PID490800, ночной тест завершён

- scripts/audit_follow_stage14_night_closed.py: первый проход остановлен UNEXPECTED_ADDITIONS (два архива логов), исходный snapshot сохранён. Архив20:22:26 — точный прежний enshrouded.log включая file identity; архив20:24:02 отдельно изучен, SHAcddeea7a…, содержит промежуточный старт17:22:26UTC и штатный shutdown. Текущий лог начинается17:24:02UTC. Общий post_close_v2 не изменялся; второй архив проверен отдельным узким правилом по фиксированному SHA/содержимому, ограничение доверия отражено в отчёте.
- Повторный аудит exit0: POST_CLOSE_INTEGRITY_PASS_FOLLOW_STOPPED / NIGHT_BUSY_NO_MOVEMENT. Оригиналы67/67,shadow77/77,31 неизменяемый installed-файл целы; новый lock отдельно подтверждён SPENT!. Backup28/28, прежняя история112/intent/SPENT/журналы сохранены. LOCAL23, добавлений/удалений0, content7/metadata8;8 world-save событий. Имена сохранены, пустых/связанных файлов нет; семантическая целостность saves не доказана. Никакого восстановления/удаления нет.
- Итог Follow: контроллер стартовал, NPC не двигался (одна позиция во всех66 samples), команд/принятых/успешных0, Ground/Path0. Дистанция4.8905–8.5271м менялась только от игрока.64 WAITING_FOR_NPC, ai_state8/decision5 во всех66 samples; ночь подтверждена пользователем. Пороги20/50, home/leash и вертикальные маршруты NOT_TESTED.
- Отчёт docs/STAGE10_14_NIGHT_TEST.md и compatibility/experiments/stage10_14/post-close-490800.json. Новый baseline runtime/stage10_14/session490800/post-close-reviewed/inventory.json SHA4e4e693d45581c004faa9f494252ec0c08d0ceced8cfe9004b1702f3b85edd45. Полные тестовые наборы не повторялись: код движения не менялся, выполнен фактический read-only аудит.
- Подготовлен план дневного повтора: отдельные token/lock/journal без сброса истории; минимальная будущая замена main.lua/follow_config.lua + новый lock, backup LOCAL23+2. Новый пакет/установка ещё не выполнялись. До расходования дневного latch read-only проверить бодрствование NPC и визуальный день, затем одна сессия. Сейчас игра закрыта, игровые файлы не менялись. Spawn_ready=false.

### 2026-11-22 — Stage10.15: причина сна подтверждена, безопасный override заблокирован

- Разобраны текущий журналPID490800 и исходники EMF0.6.18. State8=Sleep,decision5=WantsToSleep; Lua блокирует до probe, а native villager_move.paused() также ждёт при обоих признаках.66 samples/0 orders подтверждены чистым анализатором. Удаление одной Lua-проверки не решает ночное движение.
- Найдены sleepSetup→NpcCommon.sleepTime/wakeUpTime, ShouldSleep в DecideTask/CheckInterrupts, Sleep exit/enter с анимацией/actor flags/path cleanup, отдельные roam/home/leash. Статический разбор engine_parts/ai.md относится к1269579, а установлена1287369: адреса и no-sleep интервал для текущей игры не подтверждены. Подтверждённого wake/per-NPC schedule override API нет; простая запись state пропустит штатный переход.
- Реализация независимости от суток НЕ завершена: BLOCKED_NO_VERIFIED_PER_NPC_SCHEDULE_OVERRIDE. Не выдан эксперимент с выдуманными значениями за исправление. Нужна узкая проверка текущего ShouldSleep/sleep-exit/command handler, затем per-NPC безопасный override. Installation_ready=false/runtime_ready=false, установочный payload не подготовлен из-за технического блокера.
- Добавлен read-only companion/npc_schedule.py, tests/test_npc_schedule.py, schedule-analysis.json и docs/STAGE10_15.md с точными source links/границами доказательств/планом.55/55 целевых тестов PASS0.170с: интерпретация сна/intent, наблюдаемые переходы, session/ambiguity и отсутствие ложной готовности + существующий Follow. Пробуждение/ночной Follow не тестировались как реализованные возможности.20/50 и алгоритм Follow не менялись.
- Игра/сервер не запускались, ничего не устанавливалось, игровые компоненты/сохранения не менялись, NPC не создавались. Старые SPENT/lock/intent/журналы не изменялись. Критерий «Follow в любое время» пока не достигнут. Spawn_ready=false.

### 2026-11-22 — Stage10.15: реализован обратимый override сна, Movement0.3.1

- Продолжен предыдущий этап, без повторного общего исследования. Статически разобран установленный EXE1287369, SHA5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77: совпадает с post-close baseline и не изменился после чтения. Проверены текущие ShouldSleep, общий sleep-window, Sleep enter/update/exit, SetState и NpcCommandEvent handler. EXE/DLL не запускались. Хеши PE/unwind regions и точные ссылки/VA сохранены в build1287369-sleep-evidence.json и docs/STAGE10_15_IMPLEMENTATION.md.
- Подтверждено условие sleep=tod>=sleepTime OR tod<=wakeUpTime; равные часы не отключают сон. Реализован schedule.lua: временные sleepTime25/wakeUpTime−1 только у уникального спутника, пустое окно для суток0–24 включительно. Пробуждение выполняет штатный Sleep update/exit, без записи state/decision/Actor flags и без нового события движения. Переход контролируется до15с; однократный наблюдаемый exit-reroll часов учитывается, чужие/повторные изменения останавливают сессию.
- Добавлен append-журнал исходных часов до записи, проверка flush/close/readback, восстановление принадлежащих lease полей при stop/error/heartbeat expiry, частичном отказе setter и same-session reload. При ambiguity/смене session/entity автоматическая запись запрещена; reload не возобновляет Follow. EMF file watcher отслеживает .lua/mod.json, а не .jsonl — запись журнала не провоцирует reload. Принудительное отключение Lua без f_stop остаётся ограничением: unload cleanup не гарантируется.
- Интегрированы Lua Controller и Python Runner0.3.1, обновлён whitelist версии в общем validate_context. Follow20/50 X/Z, 2м3D, маршруты и лимиты сохранены. Native home/leash, сидение/разговор и roaming не отключались; полное подавление всего расписания/поведения НЕ заявлено. Цель этой минимальной реализации — устранить ночной Sleep/WantsToSleep blocker и дать существующим штатным приказам Follow работать после пробуждения. Реальное движение ночью ещё не проверено.
- Подготовлен dist/stage10_15_movement_0_3_1, exact8: пять замен(main/follow/follow_config/mod.json/README) и три новых файла(schedule.lua, новый Follow latch, пустой schedule journal). Manifest SHAecfe74668d1aaa38ce8d40e7c41283b62d0253dbda66d3b0fa44ee3f40c550d2, effective35. Новые scripts/prepare_follow_stage15.py, install_follow_stage15.py, follow_stage15.py. Пакет привязан к EXE SHA и последнему post-close PID490800; план будущего backup28=LOCAL23+5. Backup/установка/receipt этой версии пока НЕ выполнялись.
- 180/180 целевых тестов PASS,0.623с: новый schedule, интеграция Follow/host, реальный Lua reload с журналом, day/night/midnight, native wake simulation, восстановление, timeout, смена identity, partial setter, disk failure, запрет повторного spawn/session, package pin/conflict и общий LOCAL/version validator. Полный suite не повторялся. При разработке тесты выявили отсутствующий journal в старом fixture и пропущенную0.3.1 в общем whitelist; оба исправлены. Исторический Stage14 manifest теперь сверяется с его неизменным receipt, текущие исходники — с новым Stage15 manifest. Нативные переходы в тестах моделируются; игровой успех не заявлен.
- Свежая узкая read-only проверка: closed/build PASS, payload8 PASS, текущие installed32 без изменений, LOCAL23 совпадают с baseline,81 прежний intent/runtime файл и112 spawn-history записей сохранены. EXE SHA проверен; полного повторного хеширования всех больших игровых ресурсов не было. Старые SPENT/lock/intent/журналы не сбрасывались. Git diff --check PASS. Результаты offline-validation.json.
- Статус PREPARED_NOT_INSTALLED_RUNTIME_UNVERIFIED. Игра не запускалась, ничего в неё не устанавливалось, игровые команды/прямые изменения saves не выполнялись. Код и отчёты подготовлены к commit/push в завершении задачи. Следующий шаг — отдельное разрешение на exact8 установку и одну новую ночную сессию Stage10.15: подтвердить штатное вставание, фактическое сближение и восстановление часов. Spawn_ready=false.

### 2026-11-22 — Stage10.15: Movement0.3.1 установлен, ожидание ручного запуска

- По разрешению пользователя выполнен scripts/install_follow_stage15.py --install-approved, exit0. Свежий closed/build preflight, EXE и полный baseline игровых файлов/LOCAL PASS; пакет и public manifest SHAecfe74668d1aaa38ce8d40e7c41283b62d0253dbda66d3b0fa44ee3f40c550d2 совпали. Реализация и игровой payload не перерабатывались.
- Создан и проверен новый backup runtime/backups/stage10_15-movement_0_3_1:28/28 файлов (LOCAL23 + пять заменяемых),655550 байт. Backup manifest SHA48336b13c32f3a2e2d1f184368e85bf23207d3948ff4ea47c7d8ab80a53d51ef. Существующие backup и история сохранены.
- Установлены ровно8 файлов: пять замен main.lua/follow.lua/follow_config.lua/mod.json/README.md и три добавления schedule.lua/follow-stage10-15.lock/schedule-stage10-15.jsonl. Проверены effective35/35, остальные257 игровых файлов и LOCAL23 остались без изменений относительно baseline. Сохранены81 прежний intent/runtime файл и112 записей spawn-history; старые SPENT/lock/intent/журналы не сбрасывались. Новый latch UNUSED, журнал расписания пуст, Follow ещё не запускался.
- Receipt runtime/stage10_15/installation/receipt.json и compatibility/experiments/stage10_15/installation/receipt.json: INSTALLED_READY_FOR_MANUAL_START, runner_ready=true. Restore/removal dry-run PASS, откат не выполнялся. Новый baseline runtime/stage10_15/installation/inventory-after.json SHA db3f1e81c73c70d0c679756f527fab9dc2ae56d2e7aebab7899a400be96b0b71. Повторный полный suite не запускался: код не менялся;180 офлайн-тестов из предыдущей записи остаются историческим результатом.
- Игра/сервер самостоятельно не запускались; spawn/destroy/move/Bridge не вызывались, saves напрямую не менялись. Пробуждение и реальное ночное Follow пока НЕ проверены. Ожидаем ручной запуск LOCAL Body Test / AI Body Test slot1/1 и сообщение «загрузился»; затем уже разрешена ровно одна Stage10.15 сессия без MOVE, с проверкой восстановления исходных часов при остановке. При неудаче повторной сессии нет; мод до подтверждённого восстановления не отключать. После «закрыл» — короткий аудит и публикация результатов в GitHub. Spawn_ready=false.

### 2026-11-22 — Stage10.15: PID507224, ночное пробуждение подтверждено; остановка с незавершённым восстановлением

- После «загрузился» выполнен scripts/follow_stage15.py с pinned manifest и --authorized-session. Проверены installed35, прежняя история, EXE, Bridge0.3.1 и LOCAL Body Test / AI Body Test slot1/1. Единственный NPC1025, session bc857aad353566f2-1, PROFILE_ONLY. Ровно одна сессия; повтор не выполнялся.
- В21:15:20.759 при игровом времени1.9526445855ч acquired исходные sleep21.485403060913086/wake7.210055351257324. Зафиксированы SCHEDULE_SLEEP_EXIT_REAPPLIED и SCHEDULE_AWAKE_OBSERVED в21:15:21.899: state8/decision5 → state5/decision2. Пробуждение ночью подтверждено отдельно от движения.
- Ground/Path прошли, принята одна villager_move id1. На последнем PROGRESS смещение NPC от начала приказа7.2295м, расстояние до фиксированной цели1.8041м (с8.974м при выдаче); до игрока8.5863м, игрок также двигался.11 SAMPLE, дистанции3.9712–10.3265м. Достижение цели/успешное завершение приказа и устойчивое Follow не подтверждены; пороги20/50 не покрыты. Native roaming был активен до приказа.
- В21:15:34.382 CANCEL_REQUEST вызвал вложенный native callback; EMF move_bindings.cpp:89 увеличивает generation, вследствие чего follow.lua:33 использует уже недействительный world. Runner exit1/REFUSED, контроллер STOPPED/REQUEST_ERROR. Очистка тем же world не смогла повторно проверить identity: SCHEDULE_RESTORE_PENDING/IDENTITY_UNAVAILABLE. Журнал остался ACQUIRED, RELEASED отсутствует. Восстановление исходных часов НЕ подтверждено; повторный f_stop при STOPPED вернулся бы без cleanup, watchdog также пропускает STOPPED.
- Read-only f_status и Bridge log сохранены runtime/stage10_15/session507224/runtime-diagnostics.json; исходный test-session.jsonl не изменялся после завершения Runner. Снимок schedule journal и конкретный schedule-recovery-plan.json сохранены там же. SPENT/intent не сбрасывались, мод/игра не отключались, установленные Lua не изменялись.
- Для восстановления в той же session подготовлен вариант однократной адресной перезагрузки существующего Lua-мода через изменение только mtime main.lua при неизменных байтах/SHA; EMF watcher подтверждён host.cpp:1302, уже установленный on_tick recovery восстановит журналируемые часы после повторной проверки unique identity. Это ещё НЕ выполнено: требуется отдельное разрешение на перезагрузку до подтверждённого восстановления, поскольку пользователь явно запретил отключение мода до него. Следующий шаг — согласовать recovery; затем подтвердить RELEASED/SCHEDULE_RESTORED. Игра пока открыта, post-close audit/GitHub ожидают её закрытия. Spawn_ready=false.

### 2026-11-22 — Stage10.15: разрешённое восстановление расписания после ошибки

- Пользователь отдельно разрешил восстановление через перезагрузку. Выполнен runtime/stage10_15/session507224/recover_schedule.py, exit0: прежние protected history/intent и installed content hashes проверены, NPC FOUND_ONE в той же session/entity, активного villager order нет, контроллер STOPPED. Перед действием записан recovery-intent.json.
- Изменено только mtime установленного main.lua:1795371123875534000 →1795371533110078300. Байты и SHA97f1802e07adeaac7cbb5175c0862c145c788429c7e9dd8d83eb392b0d50d920 неизменны. EMF перезагрузил только aic_companion_movement в21:18:53.425; встроенный recovery выполнил SCHEDULE_RESTORED в21:18:53.443. К исходному ACQUIRED добавлен ровно один RELEASED для прежней session/entity. Предупреждений о чужих значениях часов нет; штатный release проверил readback исходных sleep21.485403060913086/wake7.210055351257324. Следующий discover показывает state8/decision5 — штатное ночное поведение снова активно.
- Проверены все файлы каталога мода: содержимое изменилось только у append-журнала расписания, SHA a330559a08247da4bc1767693f569e2c08a8b91c0f09de2398291a543af9d567. Старые locks/SPENT/intent сохранены, Stage15 latch остаётся SPENT, новый Follow/move не запускался. Receipt не редактировался; разрешённое изменение metadata main.lua записано отдельно для post-close audit. Результат SCHEDULE_RESTORED_SAME_SESSION, evidence recovery-result.json/recovery-logs.json.
- Ночное пробуждение и движение по одному приказу подтверждены, устойчивое Follow и автоматическое восстановление при исходной ошибке НЕ прошли. Нужна последующая правка обработки вложенного cancel callback и cleanup после STOPPED; сейчас код не исправлялся и новая версия не устанавливалась. Можно закрывать игру вручную. После «закрыл» выполнить короткий аудит и публикацию результатов в GitHub; без повторной сессии и rollback.

### 2026-11-22 — Stage10.15: post-close PID507224 завершён, отчёт ночного теста

- После сообщения «закрыл» подтверждено отсутствие игры/сервера, build без изменений. scripts/audit_follow_stage15_closed.py exit0: POST_CLOSE_INTEGRITY_PASS_SCHEDULE_RESTORED / NATIVE_WAKE_CONFIRMED_FOLLOW_ABORTED. Выполнено свежее полное хеширование baseline; оригиналы67/67,shadow77/77 целы. Effective35 учтены:33 содержимых неизменны, два runtime-файла подтверждены как SPENT и ACQUIRED→RELEASED; разрешённое изменение только mtime main.lua проверено по recovery-result. Receipt не редактировался.
- Backup28/28,112 spawn-history записей,81 прежний intent/runtime файл сохранены. LOCAL23: added/removed0, content8/metadata9,13 world-save событий; имена Body Test/AI Body Test сохранены, пустых/связанных файлов нет. Семантическая целостность saves не заявлена. Прямой записи/восстановления сохранений, rollback, spawn/destroy и повторной Follow-сессии не было.
- post_close_v2 ATTRIBUTION_PASS: новый backup/enshrouded_2026-11-22T21-13-43.log — точное переименование прежнего лога, chain_status — пустой тот же файл с новым временем; остальные изменения объяснены логами и отдельно проверенными runtime-файлами. Новый baseline runtime/stage10_15/session507224/post-close/inventory.json SHA aaf088bd87def15f73fe10a349831af4477fbbdfc1e1d1ad4de9d2260b8593ab.
- Итог: пробуждение ночью за1.14с подтверждено;1 intent/1 accepted/0 подтверждённых arrived. NPC сместился7.2295м после приказа, расстояние до цели8.976815→1.804144м (уточнение раннего округления8.974 в записи выше). Дистанция до игрока зависит также от движения игрока;11 SAMPLE3.9712–10.3265м. Устойчивое Follow и переходы20/50 NOT_CONFIRMED/NOT_COVERED. Часы восстановлены после отдельного разрешённого recovery, автоматическая очистка при исходной ошибке не прошла.
- Подготовлены docs/STAGE10_15_NIGHT_TEST.md, compatibility/experiments/stage10_15/post-close-507224.json и read-only audit script. Исторический implementation report снабжён ссылкой на runtime-результат. Код движения не менялся, полный suite без необходимости не повторялся; фактический аудит и git diff --check PASS. Следующий шаг — минимальная правка callback lifetime при cancel и deferred cleanup после STOPPED с целевым regression-тестом; новая установка/сессия не выполнялись. Результаты этой задачи публикуются в GitHub. Spawn_ready=false.

### 2026-11-22 — Stage10.16: Movement0.3.2 подготовлен, cancel и cleanup исправлены офлайн

- Отмена перенесена из команд в очередь server tick. Перед единственным native cancel проверяются identity и принадлежность приказа; после вызова старый world больше не читается. Следующий свежий tick подтверждает отсутствие отменённого приказа, до этого новые приказы блокируются. Отказ/исключение/timeout5с останавливают Follow без повторного cancel; чужой приказ не отменяется. Маршруты, native navigation,20/50 X/Z,3D proximity и лимиты сохранены.
- stop() теперь меняет только Lua state и не требует валидного world. STOPPED не выключает cleanup: свежие ticks восстанавливают принадлежащий lease после проверки прежнего NPC/session. cleanup NONE/PENDING/DONE отделён от Follow state; временные отказы проверки/записи оставляют PENDING с повторной проверкой не чаще1с, без новых move. При доступном прежнем NPC и работающем API/журнале штатный REQUEST_ERROR восстанавливается без reload. Потеря identity, принудительное завершение процесса или постоянный отказ API/диска остаются ограничениями, принудительной записи в чужой NPC нет.
- Runner0.3.2 после stop/error ограниченно читает f_status (до8с/16 запросов), не повторяет команды движения/stop; явно записывает cleanup CONFIRMED/UNCONFIRMED и исходную ошибку Runner. Lua schedule.lua/native wake не изменены. Новая отдельная сессия Stage16: token/lock/schedule journal/Python journal, без сброса Stage13–15 истории.
- 194/194 целевых теста PASS0.798с. Новые regression моделируют generation invalidation синхронного cancel callback, продолжение со свежим world, REQUEST_ERROR и native move/cancel failure, восстановление без reload, cancel timeout/no retry, чужой приказ, временную потерю identity и disk failure. Реальный Lua-host fixture подтверждает append ACQUIRED→RELEASED и сохранение старых SPENT/journal/intent. Старые тесты20/50/маршрутов/дня-ночи/полномочий также PASS. Первый расширенный запуск обнаружил устаревшее имя журнала в discovery fixture; исправлено. Полный suite не повторялся, нативные callbacks моделируются, игровой успех0.3.2 не заявлен.
- Пакет dist/stage10_16_movement_0_3_2 и exact manifest SHA c4fd95db4d72a2ca90834f0f5769cef2d79b7a26afe1c1a2c1bdc73a2f938804:7 операций, пять замен(main/follow/follow_config/mod.json/README) + два новых файла(follow-stage10-16.lock/schedule-stage10-16.jsonl); effective37. Подготовлены prepare/install/follow_stage16.py. Будущий backup28=LOCAL23+5, сейчас не создавался. Baseline принят из post-close PID507224 SHA aaf088bd87def15f73fe10a349831af4477fbbdfc1e1d1ad4de9d2260b8593ab.
- Свежая узкая read-only проверка: closed/build/EXE/payload7 PASS, текущие installed35 содержимых и LOCAL23 совпадают с baseline,128 прежних runtime/intent файлов и112 spawn-history записей сохранены. Полного повторного хеширования больших ресурсов не было; установщик выполнит его перед записью. Ничего в игру не устанавливалось, игра/сервер/Bridge не запускались, игровые commands/saves/старые locks не изменялись. Статус PREPARED_NOT_INSTALLED_RUNTIME_UNVERIFIED.
- Отчёт docs/STAGE10_16.md, preparation-check.json и offline-validation.json подготовлены к публикации с кодом/тестами. Git diff --check PASS. Следующий шаг — отдельное разрешение установки exact7, затем отдельная ночная сессия с реальным retarget/cancel и подтверждённым SCHEDULE_RESTORED без reload; автоматически не запускать. Spawn_ready=false.

### 2026-11-22 — Stage10.16: Movement0.3.2 установлен, ожидание ручного запуска

- Пользователь разрешил установку готового пакета и одну новую Stage16 сессию после «загрузился». Также разрешены самостоятельный анализ и подготовка следующих исправлений после теста без нового ТЗ; следующие установки/сессии требуют отдельного разрешения, одноразовые сессии не переиспользовать. Цель — минимум3 минуты реального Follow, включая ночь и повороты. Подробные логи сохранять локально, публиковать краткий отчёт и код; после «закрыл» короткий аудит важных файлов.
- scripts/install_follow_stage16.py --install-approved завершился exit0. Fresh closed/build/EXE/exact7 preflight PASS, public/package manifest SHA c4fd95db4d72a2ca90834f0f5769cef2d79b7a26afe1c1a2c1bdc73a2f938804 совпал. Выполнены предусмотренные установщиком полный baseline до/после и проверка защищённой истории; код/manifest не перерабатывались.
- Создан verified backup runtime/backups/stage10_16-movement_0_3_2:28/28 файлов,658474 байт, LOCAL23+пять замен. Backup manifest SHA2a7936d15144ef5df01e15c076b5290fb01974d19e9dc6fcf47a8a6685865c2e. Установлены ровно7 файлов (5 замен/2 добавления); effective37/37 PASS. Остальные261 игровых файлов и LOCAL23 неизменны.128 прежних runtime/intent файлов и112 записей spawn-history сохранены, старые SPENT не сбрасывались, Stage16 latch UNUSED.
- Receipt runtime/stage10_16/installation/receipt.json и compatibility/experiments/stage10_16/installation/receipt.json: INSTALLED_READY_FOR_MANUAL_START, runner_ready=true, rollback dry-run PASS; откат не выполнялся. Новый baseline runtime/stage10_16/installation/inventory-after.json SHA8911884e4bcd50fd6ffefe7cde97635a6839fea3faa64dbd30c06cd2b4d29cbc. Подготовительные194 теста не повторялись: код не менялся.
- Ограничение готового пакета сообщено пользователю: Runner останавливает движение примерно через175с, оставляя запас до native-контракта180с. Поэтому строгие минимум180с непрерывного Follow этим тестом не доказываются; длительность требуется учесть в следующем патче, не менять молча согласованный payload/лимиты текущей одноразовой сессии.
- Игра/сервер самостоятельно не запускались, Bridge/движение/spawn не вызывались, saves напрямую не менялись. Следующий шаг — ручная загрузка LOCAL Body Test/AI Body Test slot1/1 и «загрузился», затем проверить PID/контекст/версию и автоматически выполнить ровно одну scripts/follow_stage16.py --authorized-session с новым PID и pinned manifest, без MOVE. Подтвердить реальное движение, cancel без REQUEST_ERROR и отдельное восстановление часов. После «закрыл» аудит, анализ и подготовка следующей необходимой правки; публикация результатов в GitHub. Spawn_ready=false.

### 2026-11-22 — Stage10.16: PID516568, Follow заблокирован оставшимся решением сна; cleanup сработал

- После «загрузился» выполнены проверки PID516568, LOCAL Body Test/AI Body Test slot1/1, Bridge/version0.3.2, effective37 и защищённой истории. Ровно одна разрешённая Stage16 сессия, session e0057ab639c83ebe-1. START22:19:51.770; повторов нет, новый latch израсходован, прежние SPENT/intent не сбрасывались.
- SCHEDULE_ACQUIRED→SCHEDULE_SLEEP_EXIT_REAPPLIED; NPC вышел из Sleep и перемещался в рамках native поведения, но decision5 сохранился во всех13 samples (state8/13/7/3). Поэтому SCHEDULE_WAKE_TIMEOUT22:20:06.013 и STOPPED/SCHEDULE_ERROR. Orders0/probes0/recoveries0: движение NPC не доказывает Follow. Дистанция0.95075–15.70552м; устойчивое Follow, отмена и пороги20/50 не испытаны.
- Автоматический cleanup со свежего tick подтверждён без reload: SCHEDULE_RESTORED/CLEANUP_COMPLETE22:20:06.026, cleanup=DONE, журнал ACQUIRED→RELEASED. Исходные часы21.43053436279297/7.1286516189575195 восстановлены. REQUEST_ERROR не зарегистрирован, но cancel-путь не был достигнут. Exit0 Runner не означает успешное Follow.
- Сохранены runtime-result.json, runtime-diagnostics.json и снимок schedule-journal-runtime.jsonl в runtime/stage10_16/session516568; исходный test-session.jsonl сохранён. Подготовлен docs/STAGE10_16_NIGHT_TEST.md. Узкий анализ уже имеющегося исходника подтвердил native pause по decision5; убрать только Lua gate недостаточно. Reset/type0 отвергнут из-за побочных записей saved/transform; type1 — кандидат для следующего ограниченного исправления, пока не реализован и не отправлялся.
- Код/установленные моды в ходе диагностики не менялись, новых игровых команд после остановки не отправляли, выполнен только read-only status/log. Тестовые наборы повторно не запускались: сейчас собраны реальные runtime-данные. Post-close audit ожидает сообщения «закрыл»; далее по ранее данному разрешению подготовить минимальное исправление, целевые тесты и публикацию. Новая установка/сессия не разрешены. Spawn_ready=false.

### 2026-11-22 — Stage10.16: публикация промежуточного результата по запросу пользователя

- Проверка Git показала: код0.3.2 уже в коммите c9159d1, но receipt установки и отчёт PID516568 ещё не были закоммичены. Подготовлены к отдельному commit/push receipt, STAGE10_16_NIGHT_TEST.md и накопленные записи PROGRESS; подробные runtime-журналы и сохранения остаются локально.
- git diff --check PASS. Изменения только документальные, тесты кода без необходимости не повторялись. Post-close audit и следующее исправление ещё не завершены; публикация промежуточного отчёта не означает успешного Follow. Следующий шаг — после подтверждения закрытия короткий аудит и подготовка исправления оставшегося decision5.
