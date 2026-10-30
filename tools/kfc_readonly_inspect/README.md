# kfc-readonly-inspect

Минимальный read-only extractor для одного ресурса KFC. Исходник использует закреплённый `kfc-parser` commit `16708594d686b030d909f2d835b199d879ea9ad8`, открывает KFC через `KFCReader`, декодирует один GUID/type и пишет JSON только в stdout либо в новый файл вне каталога игры.

Текущий статус: **SOURCE_PREPARED / BUILD_BLOCKED**. В рабочей среде отсутствуют `cargo` и `rustc`; бинарник не собирался и не запускался. Никакой бинарник в репозиторий не включён. Требуется Rust 1.88. Установка toolchain, сборка с сетевой загрузкой зависимостей и чтение игровых KFC должны согласовываться отдельно.

После появления проверенного локального toolchain предполагаемая команда сборки:

```powershell
cargo build --release --manifest-path tools/kfc_readonly_inspect/Cargo.toml
```

Запуск без output выводит JSON в stdout. Если указан output, существующий файл не перезаписывается, а путь внутри каталога игры отклоняется. В исходнике отсутствуют KFC writer/patch API.
