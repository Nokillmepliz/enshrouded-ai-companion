# Этап 10.5 — аудит KFC Inspector, контрольная точка A

Дата: 2026-11-01. Статус: **CHECKPOINT_A_COMPLETE / BLOCKED_TOOLCHAIN**. Выполнены только разрешённые аудит, усиление исходника и синтетические тесты. Rust не устанавливался, inspector не собирался и оригинальные ресурсы по GUID не читались.

## Toolchain и совместимость

| Проверка | Фактический результат |
|---|---|
| `rustc`, `cargo` | `NOT_FOUND` |
| `cl.exe`, `link.exe`, `clang-cl`, `gcc`, `cmake`, `ninja` | `NOT_FOUND` |
| Visual Studio / Build Tools | install path и registry registration не найдены |
| Edition | `2024` |
| MSRV инспектора | `1.88` |
| MSRV pinned kfc-parser | `1.88.0` в workspace commit `16708594d686b030d909f2d835b199d879ea9ad8` |
| Rust 1.88 | Совместим по manifest/MSRV; фактическая компиляция ещё не выполнена |

Edition 2024 стабилизирован в Rust 1.85, но pinned upstream требует именно 1.88.0. Официальный Rust для Windows рекомендует MSVC build tools; target `x86_64-pc-windows-msvc` также требует host tooling. Источники: [Rust install](https://rust-lang.org/install), [архив официальных standalone installers 1.88.0](https://forge.rust-lang.org/infra/archive-stable-version-installers.html), [Windows MSVC target](https://doc.rust-lang.org/rustc/platform-support/windows-msvc.html), [Rust 1.85 release notes](https://doc.rust-lang.org/releases.html#version-1850-2025-02-20).

## Dependencies

Прямые зависимости ограничены `anyhow`, `serde_json` и `kfc` с git URL и точным `rev=16708594d686b030d909f2d835b199d879ea9ad8`; включён только feature `resource`. Pinned upstream `Cargo.lock` v4 фиксирует среди необходимой цепочки:

| Package | Версия upstream lock | Значение для сборки |
|---|---|---|
| `anyhow` | `1.0.100` | error context |
| `serde_json` | `1.0.140` | JSON export |
| `zstd` | `0.13.3` | KFC decompression |
| `zstd-safe` | `7.2.4` | wrapper |
| `zstd-sys` | `2.0.15+zstd.1.5.7` | native dependency |
| `cc` | `1.2.48` | компиляция bundled zstd C source |

У inspector пока нет собственного `Cargo.lock`. Поэтому первая разрешённая Cargo-операция должна только создать lock; затем источники, checksums, build scripts и отличие от upstream lock проверяются до `cargo build --locked`. Наличие `zstd-sys -> cc` означает, что одного Rust toolchain недостаточно: нужен совместимый локальный C compiler/linker. В текущей машине он не найден.

## Аудит read-only режима

Pinned `KFCReader` открывает `enshrouded.kfc`, `enshrouded.kfc_resources` и DAT через `File::open`; inspector не импортирует `KFCWriter`, patch writer или API создания ресурсов. Запись возможна только для запрошенного JSON-отчёта вне game directory.

Исправлены найденные проблемы:

- game и output parent канонизируются; symlink/junction на game directory отклоняется;
- output внутри game directory, существующий output и input/output collision отклоняются;
- `OpenOptions.create_new(true)` закрывает перезапись и гонку с созданием существующего пути;
- JSON полностью строится до создания output;
- при ошибке `write/flush/sync_all` удаляется только новый частичный report вне game directory;
- обязательные input открываются только для чтения;
- добавлены toolchain, manifest, source и upstream-lock audits.

В Rust source нет `unsafe`, временных файлов, логов, сетевых операций или удаления игровых файлов. `remove_file` применяется только к новому output при ошибке его финализации. Rust unit tests подготовлены для запрета output внутри игры и защиты существующего отчёта, но не запускались без toolchain.

## Выполненные и невыполненные проверки

- Проверен фактический 96-байтовый header оригинального `enshrouded.kfc`: magic `KFC4`. Это был ограниченный read-only header check, не resource lookup.
- Размеры обнаруженных inputs: KFC `9,392,128`, resources `214,536,192`, EXE `35,338,312` байт.
- Resource index, hunter/blacksmith, registries и зависимости: **NOT_EXECUTED**.
- Pre/post SHA-256 игровых файлов: **NOT_EXECUTED**, потому что inspector ещё не запускается. Их нужно снять непосредственно перед и после разрешённого чтения в части C.
- Binary SHA-256: **NOT_EXECUTED**, бинарника нет.
- Игра, EML и spawn: **NOT_EXECUTED**.
- Python/offline suite: **216 PASS, 1 SKIP**; `compileall` и `git diff --check` PASS. Skip — ОС не разрешила создать тестовый directory symlink; перед частью C это должно быть повторено с доступным junction/symlink fixture.

## План после отдельного разрешения

1. Сначала решить блокер native compiler/linker. Установка только Rust 1.88 не позволит собрать `zstd-sys`.
2. Получить Rust 1.88.0 только из официального источника, проверить подпись/checksum и использовать process-local `RUSTUP_HOME`, `CARGO_HOME`, `CARGO_TARGET_DIR`; передать `--no-modify-path`. Никакой глобальный PATH не менять.
3. Создать lock локальным Cargo, проверить его и все build scripts; дальнейшие команды выполнять с `--locked`.
4. Запустить Rust unit tests и fixture tests. При любом отказе safety-теста остановиться.
5. Собрать в `.tools/kfc-inspector`, вычислить SHA-256 EXE и проверить imports/signature metadata.
6. Снять полный baseline KFC/resources, DAT, игровых DLL и обоих наборов saves. После единичного read-only lookup повторить и потребовать полное совпадение.
7. Сначала прочитать один hunter resource, затем blacksmith; отчёты писать только в ignored `runtime/research/stage10_5/`.

Части B/C не начаты: текущего запроса недостаточно для установки Rust или дополнительного native toolchain.
