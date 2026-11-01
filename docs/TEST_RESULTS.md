# Результаты подготовки этапа 2

## Этап 10.5 — части B/C

- Local Rust/Cargo 1.88.0 и MSYS2 GCC 16.2.0/ld 2.47: установлены в `.tools`, системный/user PATH и Rust env не изменены.
- `Cargo.lock`: 42 package entries, crates.io checksums и pinned KFC commit проверены; активные build scripts проверены до build.
- `cargo test --locked`: **2 PASS**; release build: PASS; binary SHA-256 `fb106699dd0edad8afa5d39b4264c3ed29652099882a573cfd6f207db49be0c8`.
- Python suite после изменений: **218 PASS, 1 SKIP**. Skip — privileged directory symlink; отдельный unprivileged Windows junction test: PASS.
- Negative binary cases: malformed GUID, missing GUID и unknown resource type корректно завершились с code 2 без создания output.
- Read-only KFC: hunter/blacksmith, preset collection, item registry, 24 target ItemInfo, 35 RenderModel и общий 102-joint hierarchy декодированы.
- Integrity: **210/210 файлов идентичны** до/после (`added=[]`, `removed=[]`, `changed=[]`).
- Игра/EML не запускались, игровые файлы, saves и entities не изменялись. Canonical fingerprint не повышен выше `STRUCTURAL_MATCH=true`; `spawn_ready=false`.

## Этап 10.5 — историческая контрольная точка A

Фактически выполнены Python safety/audit tests и полный offline suite: **216 PASS, 1 SKIP**. Skip относится к созданию Windows directory symlink без доступной привилегии; canonical path guards проверены остальными fixtures, а реальный junction/symlink test остаётся gate части C. `compileall` и `git diff --check` прошли. Rust unit tests, Cargo lock/build/test, binary audit, KFC GUID lookup и игровые integrity hashes имеют статус `NOT_EXECUTED`: toolchain отсутствует и установка не разрешена.

Текущий environment audit: `rustc/cargo/cl/link/clang-cl/gcc/cmake/ninja=NOT_FOUND`; manifest и pinned upstream lock прошли статическую проверку. `zstd-sys -> cc` подтвердил обязательность native C compiler. Оригинальный KFC использовался только для ограниченного read-only KFC4 header check; resource data не извлекались.

## Этап 10.4

Добавлены тесты reflection schema, полей/типов шести компонентов, corrupt reflection, structural/resource/dependency levels, GUID validation, mismatch, stable SHA-256 и safety envelope KFC inspector. Preflight tests отклоняют повреждённый KFC header и output в game directory и проверяют неизменность входов. Реальная Rust-сборка/декодирование не выполнялись из-за отсутствия toolchain и не считаются PASS.

Полный suite: **205 PASS**. `compileall`, Lua validation существующих модов и `git diff --check` прошли. Rust source не компилировался из-за отсутствия cargo/rustc и не считается проверенным бинарником. Игровых проверок этапа 10.4 нет.

## Этап 10.3

Добавлены регрессии typed evidence v2 и Lua patch для `CONFIRMED`, отсутствующего component, отсутствующего field и неожиданного GUID-object/table. Evaluator проверяет UUID, status/type/path, source/clone mismatch, ручной `model_match`, старый формат и nil-like значения. Observer измеряется вместе с префиксом ответа и ограничен 1023 байтами.

Полный suite: **193 PASS**. `compileall`, Lua compile (через Lupa) и `git diff --check` прошли. Все `status`/`inspect`/`compare` декодируются как JSON и в worst-case fixture укладываются в 1023 байта. Игровой тест не выполнялся; исторические 188 PASS этапа 10.2 не выдаются за текущий runtime результат.

## Этап 6 — Human Body research, 30.10.2026

- `.tools/python/python.exe -m unittest discover -s tests -q`: **97 тестов, PASS**.
- `.tools/python/python.exe -m compileall -q companion scripts tests`: PASS.
- `git diff --check`: PASS.
- `scripts/package.py`: архив содержит новый `body_profiles.lua`, выключен по умолчанию и воспроизводим; SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`.
- Десять новых тестов проверяют каталог human candidates, запрет runtime-выбора, capabilities, missing/partial/delayed fingerprint, reflection timeout, identity change/EntityId reuse, exact-current-observation перед удалением и изоляцию legacy Vukah GUID.
- Все прежние 87 тестов сохранены, включая partial spawn/dismiss, faction failure, unknown outcome, runtime.lock/reload и запрет удаления untrusted entity.
- Старые GUID тела/маркера вынесены в `body_profiles.lua` как `legacy_vukah`; runtime-поведение protocol 1 / `safety_revision=2` не менялось.
- Human runtime adapter, spawn, movement, inventory и equipment **не реализованы**. Тесты подтверждают fail-closed офлайн-политику, а не работу humanoid в Enshrouded.
- Игра не запускалась; файлы игры и сохранения не менялись.

## Актуальное техническое ревью — 30.10.2026

- Полный запуск `.tools/python/python.exe -m unittest discover -s tests -q`: **87 тестов, PASS** (56 прежних с уточнёнными ожиданиями и 31 новый тест).
- `.tools/python/python.exe -m compileall -q companion scripts tests`: PASS.
- `git diff --check`: PASS.
- `scripts/package.py`: ZIP пересобран; SHA-256 `c40603f062b6a55b2a3c79fb31cfee4172a8f26f93ed676d23cc33450c8c3e91`.
- Текущая ревизия безопасности адаптера: **safety_revision=2**, protocol=1. Новый Python-клиент отказывает в игровых изменениях через старую ревизию.
- В тестах используется настоящий Lua 5.4 через Lupa и поддельный EMF. Отдельно проверены реальные Lua операции с lock во временном каталоге; игровых файлов это не касается.
- Изучены локальные исходники EMF на commit `08d600155fcadc8e45cc9c6f3932a67c717345be`: нативные spawn/destroy, Lua bindings/host, EntityId, SpawnTime, StoredSceneId и перечисление WorldView. Проверяемого generation ID экземпляра для наших шаблонов не найдено; ссылки и ограничения — в [PROTOCOL.md](PROTOCOL.md).
- EMF не установлен, игра не запускалась, bridge к игре не подключался, игровые файлы и сохранения не изменялись. Игровые проверки: **NOT RUN**.

Ниже сохранена история прошлых запусков и старых хешей архива; для текущего испытания использовать результат выше.

Обновление этапа 3 от 30.10.2026: **56 тестов PASS**, `compileall` PASS. Добавлены логи клиента/адаптера и проверяемое резервирование. Текущий архив имеет SHA-256 `e9fb551e69bed8ba2f26884436b3b9c6c7b4bf4bea48df3a67d8641778e391ff`; приведённый ниже хеш относится к предыдущему архиву этапа 2. [Подробный текущий отчёт](STAGE3_PREFLIGHT.md). DLL EMF отсутствуют; в игре ничего не проверялось.

Дата: 30 октября 2026 года.

## Выполнено без игры

- `python -m unittest discover -s tests -q`: **48 тестов, PASS**.
- `python -m compileall -q companion scripts tests`: PASS.
- `python -m companion --help`: CLI доступен, подключения к игре нет.
- Проверены 87 ссылок на upstream-исходники (существование файлов и границы строк), относительные ссылки документации и отсутствие пробелов на концах строк исходников.
- `python scripts/package.py`: создан `dist/aic_body-0.1.0.zip`; тест архива проверяет состав, disabled manifest и воспроизводимость.
- Проверен SHA-256 включённого Python bridge; функционально он не изменялся.

Среда: Windows, изолированный Python 3.12.10 в `.tools/python`, Lupa 2.6 с Lua 5.4. Для Lua запускается настоящий код `main.lua`/`body.lua`/`json.lua`; EMF, файлы мода и мир подменены тестовой средой. Системная установка Python не изменялась. `.tools` исключён из Git.

SHA-256 подготовленного архива:

```text
d51908d0dc32e341f1195168df07009ed2685580dd545746acd0ff5f7e8ef00e  aic_body-0.1.0.zip
```

## Не выполнялось

Установка EMF/адаптера, включение bridge, подключение к игровому процессу, изменение файлов игры/сохранений, запуск мира, спавн реальной сущности и игровые испытания. Наличие ModelResource на выбранных теле/маркере, работа reflection на установленной версии и длительное физическое следование пока не подтверждены.

Следующий этап — [FIRST_RUN.md](FIRST_RUN.md) и [TEST_PLAN.md](TEST_PLAN.md), отдельно после подтверждения пользователя. Текущий результат подтверждает логику прототипа и его контракт, а не работу внутри игры.


## Этап 7 — Player Character Companion, 30.10.2026

- `.tools/python/python.exe -m unittest discover -s tests -q`: **110 тестов, PASS**. Сохранены прежние 97 и добавлены 13 тестов player-character policy.
- `.tools/python/python.exe -m compileall -q companion tests scripts`: **PASS**.
- `.tools/python/python.exe scripts/package.py`: **PASS**; две последовательные сборки дали одинаковый SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`.
- Новый `companion/player_character.py` — только офлайн evidence/identity/authority policy. Он не входит в Lua-архив, не подключается к игре и не включает runtime-команды.
- Read-only анализ сохранений ограничен метаданными файлов. Save-файлы, Steam ID, игровые бинарники и приватные логи в Git не добавлены.
- Игра, второй клиент, spawn, input, inventory operations и AI Brain не запускались.

## Этап 8 — Independent Humanoid, 30.10.2026

- `.tools/python/python.exe -m unittest discover -s tests -v`: **126 тестов, PASS**. Сохранены прежние 110, добавлены 16 тестов independent lifecycle, read-only policy и компиляции Lua survey.
- `.tools/python/python.exe -m compileall -q companion tests scripts`: **PASS**.
- `git diff --check`: **PASS**.
- `scripts/package.py`: **PASS**, legacy-пакет `aic_body` не изменился, SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`. Survey является отдельным исходным модом и в этот ZIP не включён.
- `companion/independent_humanoid.py` не подключается к игре. Все реальные descriptors уникальны и выключены; неизвестные шаблоны и операции отклоняются.
- `mods/aic_humanoid_survey` выключен по умолчанию. Статическая проверка запрещает spawn/destroy/event emission/inventory/save/tick paths; Lua syntax проверяется отдельно перед публикацией.
- Игра не запускалась, survey не устанавливался, игровые файлы/сохранения/сущности не менялись. Human spawn, movement, combat, inventory, equipment и persistence: **NOT RUN / BLOCKED**.
# Этап 9 — EML humanoid template (2026-10-30)

Среда: repository offline, `.tools/python/python.exe`, pinned EML `16708594`, EMF `08d60015`, Enshwick `13556119`. Игра и EML binary не запускались; каталог игры и сохранения не читались/не менялись.

Результаты:

- полный suite: **141 tests PASS**;
- новые Stage 9 tests: **15 PASS**, включая исполнение настоящего `src/mod.lua` через Lua 5.4/Lupa с fake EML API;
- Lua test доказал deep-copy: source story faction осталась `Vukah`, новый resource получил `PlayerAlly`, новый `npcId=2939921867`, новый GUID добавлен в fake registry;
- negative validation: unsupported layout/capability, unknown/conflicting GUID, missing source, story target, unsafe faction, autospawn, runtime command, missing marker/ownership/dismiss и runtime activation — отклонены;
- `python -m compileall -q companion scripts tests`: PASS;
- существующие Lua source compilation tests: PASS; системный `lua/luac` отсутствует (`NO_SYSTEM_LUA`), поэтому отдельный внешний `luac` не выполнялся;
- `git diff --check`: PASS.

Эти проверки подтверждают структуру EML patch и наши инварианты. Они не подтверждают, что build 1273043 загрузит новый template, что human model/animations и workshop lifecycle работают, или что entity можно безопасно создать/удалить.

# Этап 10 — подготовка load-only проверки (2026-10-31)

- Официальные `dbghelp.dll` и `emm.exe` EML 0.2.0 скачаны в ignored audit-каталог, не запускались и совпали с GitHub release digests. Оба x64 PE без Authenticode; Microsoft Defender custom scan не обнаружил угроз. Независимая воспроизводимая сборка не выполнялась.
- Реальный read-only preflight: **PASS** для Enshrouded build `1273043`, EXE SHA-256 `d64966e…`, EMF loader `53b3f6e…`, EML `dbghelp.dll` `038b7a1…`, patch и observer. Baseline DAT: `000`–`054`. Результат намеренно содержит `phase_b_allowed=false`.
- Stage 10 добавил **22 теста**; вместе с 15 тестами EML этапа 9 целевой прогон дал **37 PASS**. Полный suite: **163 tests PASS**.
- `python -m compileall -q companion scripts tests`: **PASS**. Lua patch реально исполняется в Lupa/fake EML; observer Lua компилируется. Ошибочные hashes/loader, stale evidence, running game, partial/repeated install, corrupt backup, changed rollback file и неизвестный DAT fail closed.
- Backup выполнен только как dry-run: 20 файлов, 224 556 422 байта. Реальная проверенная копия не создана.
- EML не установлен; `dbghelp.dll`, patch и observer в игру не копировались; игра не запускалась; KFC/data/save не менялись; spawn/destroy/faction/inventory не выполнялись.
- Прямой поиск нового `TemplateResource` через публичный EMF Lua недоступен без entity. Поэтому runtime-совместимость EML+EMF, writer finalization, game load и template acceptance остаются **NOT RUN**, а полный вердикт — **BLOCKED_BEFORE_PHASE_B_FULL_CRITERIA**.

# Этап 10.1 — acceptance gate A/B/C (2026-10-31)

- Все прежние **163 теста сохранены**; добавлено **19 тестов** Stage 10.1. Полный suite: **182 test PASS**. Отдельный regression test проверяет реальный tab-separated формат Lua `print()` для `AIC_EML_TEMPLATE_READY`.
- Синтетический полный набор с одним `run_token` подтверждает A/B/C и даёт `LOAD_ONLY_SUCCESS`; `spawn_ready` остаётся `false`.
- Negative tests: writer finalization отсутствует, stale token/evidence, неверные GUID/npcId/faction, неполные model/animation, observer/bridge недоступны, game/resource error, неизвестный KFC/DAT, нецелевой save изменён, backup отсутствует и rollback не готов.
- Пустой `evaluate` и CLI без артефактов возвращают `NOT_EXECUTED`; UNKNOWN не превращается в PASS.
- Установка в тестовом каталоге генерирует 128-битный token, внедряет его в patch и observer и сохраняет в receipt. Partial/repeated install и rollback protections прежних тестов проходят.
- Lua patch исполняется через Lupa только после тестовой замены placeholder; repository placeholder сам по себе fail closed. Observer Lua компилируется и остаётся read-only.
- `python -m compileall -q companion scripts tests`: **PASS**; `git diff --check`: **PASS**.
- Реальный read-only `preflight`: `PREPARATION_READY`, exact build/hashes PASS, patch/observer PASS, direct lookup `UNAVAILABLE_WITHOUT_ENTITY`. `installation_ready=false` только потому, что новый verified backup ещё не создан.
- Повторный backup dry-run: 20 файлов, 224 556 422 байта; копирование не выполнялось.
- Игровой эксперимент, установка, A/B/C runtime evaluation, изменения KFC/saves и spawn: **NOT EXECUTED**.

# Этап 10.2 — часть A (2026-10-31)

- Усиленный реальный read-only preflight: **PREPARATION_READY**; exact build/game/EMF/EML hashes, patch/observer, process, collisions, stale evidence, DAT baseline и disk-space checks PASS.
- Добавлены 2 regression tests: legacy manifest безопасно отклоняется; `eml.json`/KFC backup/EML mod/install temp/observer config/receipt collisions блокируют preflight. Stage 10 suite: **24 PASS**.
- Полный suite: **184 PASS**. `compileall`, Lua validation и `git diff --check`: PASS.
- Backup dry-run: 20 файлов, 224 556 422 байта. Реальный backup и установка не выполнялись.
- Dry-run install без нового verified manifest вернул `verified_backup_required`; rollback без receipt — `rollback_receipt_invalid`.
- A/B/C, game load, EML evidence, EMF runtime и rollback: **NOT_EXECUTED**. `spawn_ready=false`.

## Часть B

- Новый backup: **20/20 файлов verified**, 224 556 422 байта; SHA-256 копий и текущих источников совпадают, mismatch 0.
- Post-install: **9/9 receipt hashes PASS**, receipt `complete`, EML/EMF hashes PASS, run token в patch/observer, placeholders отсутствуют только в установленных копиях, install temporary отсутствуют.
- Defender/real-time protection оставались включёнными. Игра не запускалась; evidence и KFC `.bak` до первого запуска отсутствуют.
- `aic_body` исключён из receipt. Обнаружено предварительно существовавшее отличие legacy `body.lua` от текущего репозитория; оно не исправлялось и не относится к девяти установленным файлам.
- Полный offline suite после установки: **184 PASS**; `compileall` и `git diff --check`: PASS.
- Runtime A/B/C и post-run integrity по-прежнему **NOT_EXECUTED**; rollback не выполнялся.

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
# Этап 10.6, часть A — 2026-11-01

- Полный Python suite: **258 tests run: 257 PASS, 1 skipped**.
- Новые Stage 10.6 tests: **40 PASS**. Они покрывают evidence v3, все состояния typed CharacterSetup, A/V/B/C, stale token, writer finalization, component/reference/animation mismatch, integrity, compact observer и mutation API ban.
- `python -m compileall -q companion scripts tests`: **PASS**.
- `git diff --check`: **PASS**.
- KFC Inspector `cargo test --locked`: **2 PASS**.
- Реальный Stage 10.6 dry-run preflight: **PREPARATION_READY**; exact hashes/patch/observer/DAT/free-space checks PASS, blocker только `verified_backup_missing`.
- Реальные read-only hashes игры повторно совпали с baseline build 1273043; EML/patch/observer/export в каталоге игры отсутствуют.
- Runtime: **NOT_EXECUTED**. Игра не запускалась, backup/install не выполнялись, игровые файлы и saves не менялись.
