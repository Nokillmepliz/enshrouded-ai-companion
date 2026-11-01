# Этап 10.5 — KFC Inspector: сборка и результаты

Дата: 2026-11-01. Итог: **PARTIAL_SUCCESS**. Инспектор собран и безопасно прочитал выбранные ресурсы оригинального KFC. Цепочка визуальных ресурсов исходных NPC подтверждена до `RenderModel` и общего hierarchy. Совпадение этих ссылок у создаваемого EML-клона и фактический runtime render не проверялись, поэтому `spawn_ready=false`.

## Локальная цепочка сборки

Все инструменты размещены в игнорируемой Git папке `.tools`; административные права, системная установка и постоянное изменение `PATH` не применялись.

| Компонент | Фактическая версия / проверка |
|---|---|
| Rust host | `rustc 1.88.0 (6b00bc388 2025-06-23)`, `x86_64-pc-windows-gnu` |
| Cargo | `1.88.0 (873a06493 2025-05-10)` |
| GCC | MSYS2 MINGW64 `16.2.0-6` |
| GNU ld | Binutils `2.47-4` |
| rustup bootstrap | SHA-256 `d2845ad914acf5add202100c0a7ddf19ab1c3e52521e12841bafff13888e49bb`, совпал с опубликованным `.sha256`; Authenticode отсутствует |
| MSYS2 base `20260927` | SHA-256 `8a2095647afbf799d113d0cae35f7544589d059819042635504e75bd2179bd02`; detached OpenPGP `GOODSIG/VALIDSIG` |
| MSYS2 signing key | primary `0EBF782C5D53F7E5FB02A66746BD761F7A49B0EC`, signing subkey `E0AA0F031DBD80FFBA57B06D5A62D0CAB6264964` |

Источники: [официальный Rust rustup](https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-gnu/rustup-init.exe), [архив Rust 1.88.0](https://forge.rust-lang.org/infra/archive-stable-version-installers.html), [официальный MSYS2 repository](https://repo.msys2.org/distrib/x86_64/), [MSYS2 MINGW64 environment](https://www.msys2.org/docs/environments/). OpenPGP-подпись криптографически валидна, но локальный GPG сообщил `TRUST_UNDEFINED`: imported key не сертифицирован отдельной локальной цепочкой доверия. Архив получен по HTTPS с официального домена.

После установки пользовательские `RUSTUP_HOME`, `CARGO_HOME` остались пустыми, а пользовательский `PATH` не изменился. Антивирус и защита Windows не отключались.

## Cargo audit

Собственный [Cargo.lock](../tools/kfc_readonly_inspect/Cargo.lock) v4 содержит 42 package entries. Его SHA-256 на момент сборки: `b072fc08491f5c5ccda99f2cf4a793472e35a6d410a12e86c50b5ed12d6423ed`. Все crates.io entries имеют checksum; `kfc`, `kfc-base` и `kfc-resource` закреплены на commit `16708594d686b030d909f2d835b199d879ea9ad8`.

Перед сборкой исходники были получены через `cargo fetch --locked`, после чего проверены все активные `build.rs`. Они выполняют feature/version probes, генерируют файлы только в `OUT_DIR` и собирают vendored zstd через `cc`; сетевых клиентов, PowerShell/cmd, автозапуска или записи в игровой каталог не обнаружено. Неиспользуемые workspace build scripts upstream proxy/mod-loader в активный dependency graph не входят.

## Бинарник

Результат: `.tools/kfc-inspector/bin/kfc-readonly-inspect.exe`, 3 513 481 байт, SHA-256 `fb106699dd0edad8afa5d39b4264c3ed29652099882a573cfd6f207db49be0c8`. Это локальная сборка без Authenticode. Импорты: стандартные `KERNEL32`, `msvcrt`, `ntdll`, `USERENV`, `WS2_32`, Windows API sets и `bcryptprimitives`. Бинарник и `.tools` не публикуются.

Инспектор поддерживает три ограниченных read-only операции:

- декодирование одного точного GUID/type;
- перечисление GUID только одного явно указанного type;
- поиск фактического type по одному GUID.

Он не импортирует `KFCWriter`, patch writer или create/update API. Output канонизируется, запрещён внутри game directory, создаётся через `create_new(true)` и не перезаписывается.

## Проверки безопасности

- Rust unit tests: **2 PASS**.
- Полная Python suite после изменений: **217 PASS, 1 SKIP**; skip относится к symlink, требующему Windows privilege.
- Отдельный Windows junction test без admin: **PASS**, ссылка на game fixture разрешена до реального пути и output отклонён как `output_inside_game_forbidden`.
- Повреждённый/truncated KFC, неверный magic, input/output collision и существующий output отклоняются до записи.
- Реальный бинарник отдельно отклонил malformed GUID, отсутствующий GUID и неизвестный resource type с exit code 2; во всех трёх случаях output не создан.
- `cargo test --locked` и `cargo build --release --locked`: **PASS**.

Синтетический fixture не покрывает успешное декодирование минимального ресурса: pinned parser не предоставляет безопасный fixture writer без включения write-path в inspector. Успешный decode проверен отдельными точечными чтениями оригинальных ресурсов после прохождения guards.

## Чтение оригинального KFC

Игра не была запущена. Отчёты записаны только в игнорируемый `runtime/research/stage10_5`.

| Ресурс | GUID / type | Результат |
|---|---|---|
| hunter | `e3736dff-0ad2-47fc-903c-66c1775836e8`, `keen::ecs::TemplateResource` | декодирован, 81 component |
| blacksmith | `04d42ed2-beb4-4013-8f10-5d63efae2015`, `keen::ecs::TemplateResource` | декодирован, 81 component |
| character presets | `a1bea7fc-2122-4dd3-a471-2b815a65134b`, `keen::CharacterPresetCollection` | 54 presets, target IDs найдены |
| item registry | `3064d35d-7342-40ca-bdc9-aad58f83bf45`, `keen::ItemRegistryResource` | 4207 `itemRefs` и 4207 parallel `dbgNames` |
| связанные items | `keen::ItemInfo` | декодированы 24 target resources |
| visual models | `keen::RenderModel` | найдены и декодированы 35/35 target GUID |
| общий hierarchy | `87b29df6-6518-43ef-9298-e3f85a6204b9`, `keen::ModelHierarchyResource` | найден, 102 joint names |

`CharacterPresetRegistry` не является отдельным KFC type в найденной цепочке. Runtime singleton строится из одного сериализованного `keen::CharacterPresetCollection`; именно в нём `presetId` связывается с item/body references. `ItemRegistry` аналогично является runtime singleton, а его сериализованный источник — `keen::ItemRegistryResource`.

## Контроль целостности

До первого чтения и после всех чтений вычислен SHA-256 одинакового набора из **210 файлов**: 62 game files (EXE, оба KFC, 55 DAT и root DLL), 23 LOCAL save files и 125 Steam save files. Итог сравнения: `added=[]`, `removed=[]`, `changed=[]`, `identical=true`.

Ключевые исходные хеши:

- `enshrouded.exe`: `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882`;
- `enshrouded.kfc`: `54a8cb76b3229c486ef55a7ababcd48828fa0ffc5bb144d206f687fd0ab00a92`;
- `enshrouded.kfc_resources`: `53786c45797d275661f3ccc1fd8c84527a74f376e01f05fc76351f91fb17cb3d`;
- установленный EMF proxy `dinput8.dll`: `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee`.

## Ограничения

- KFC подтверждает исходные NPC, но не сериализованные ссылки будущего `aic_eml_humanoid`; этот GUID ожидаемо отсутствует в original KFC.
- `RenderEquipment.lastModels` в обоих template содержит 24 `null`: это runtime output, а не источник visual references.
- Ни clone reference equality, ни фактический render не проверены.
- Материалы внутри `RenderModel` и весь runtime selection pipeline не проверялись как отдельный полный dependency closure.
- Игра, EML, NPC и сохранения не запускались и не изменялись.

Следующий допустимый шаг — отдельный load-only эксперимент, который экспортирует у EML-клона точные `CharacterSetup` values и подтверждённые preset/item/model reference paths без spawn.
