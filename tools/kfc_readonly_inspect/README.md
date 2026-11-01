# kfc-readonly-inspect

Минимальный read-only extractor для одного ресурса KFC. Исходник использует закреплённый `kfc-parser` commit `16708594d686b030d909f2d835b199d879ea9ad8`, открывает KFC через `KFCReader`, декодирует один GUID/type и пишет JSON только в stdout либо в новый файл вне каталога игры.

Текущий статус: **AUDITED_SOURCE / BUILD_BLOCKED**. В рабочей среде отсутствуют `cargo`, `rustc` и native C compiler/linker; бинарник не собирался и не запускался. Никакой бинарник в репозиторий не включён. Pinned parser требует Rust 1.88, а `zstd-sys` требует C compiler. Установка toolchain, генерация и аудит собственного `Cargo.lock`, сборка с сетевой загрузкой зависимостей и чтение игровых KFC должны согласовываться отдельно.

После появления проверенного локального toolchain предполагаемая команда сборки:

```powershell
cargo build --release --manifest-path tools/kfc_readonly_inspect/Cargo.toml
```

Запуск без output выводит JSON в stdout. Если указан output, его canonical parent должен находиться вне каталога игры; существующий файл не перезаписывается, новый создаётся через `create_new`, а частичный report удаляется при ошибке финализации. В исходнике отсутствуют KFC writer/patch API. Результаты аудита: [STAGE10_5_KFC_INSPECTOR_RESULTS.md](../../docs/STAGE10_5_KFC_INSPECTOR_RESULTS.md).
