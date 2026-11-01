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
