# kfc-readonly-inspect

Минимальный read-only inspector для закреплённого `kfc-parser` commit `16708594d686b030d909f2d835b199d879ea9ad8`. Инструмент открывает KFC через `KFCReader`, не импортирует writer/patch API и записывает только новый JSON вне game directory.

Требования: Rust 1.88, compatible C compiler для vendored zstd и проверенный [Cargo.lock](Cargo.lock). Сборка выполняется только с `--locked`:

```powershell
cargo test --locked --manifest-path tools/kfc_readonly_inspect/Cargo.toml
cargo build --release --locked --manifest-path tools/kfc_readonly_inspect/Cargo.toml
```

Точечное декодирование одного ресурса:

```text
kfc-readonly-inspect <game-dir> <guid> <qualified-type> [output.json]
```

Индекс GUID только для одного точного типа:

```text
kfc-readonly-inspect --list-type <game-dir> <qualified-type> [output.json]
```

Определение фактического type одного GUID:

```text
kfc-readonly-inspect --lookup-guid <game-dir> <guid> [output.json]
```

Без output JSON выводится в stdout. С output канонизируется существующий parent, запрещается путь внутри game directory и перезапись; файл создаётся через `create_new(true)`. При ошибке decode output не создаётся. Инструмент и собранный EXE нельзя помещать в каталог игры.

Локальный бинарник этапа 10.5 хранится только в игнорируемой `.tools/kfc-inspector/bin` и не публикуется. Результаты аудита и контроль целостности: [STAGE10_5_KFC_INSPECTOR_RESULTS.md](../../docs/STAGE10_5_KFC_INSPECTOR_RESULTS.md).
