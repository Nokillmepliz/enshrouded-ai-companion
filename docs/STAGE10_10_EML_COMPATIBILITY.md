# Stage 10.10 — EML и content loader

Upstream EML — [Brabb3l/kfc-parser](https://github.com/Brabb3l/kfc-parser).
Последний stable **v0.2.0**, 2026-10-16; последний исследованный commit
[`16708594d686b030d909f2d835b199d879ea9ad8`](https://github.com/Brabb3l/kfc-parser/commit/16708594d686b030d909f2d835b199d879ea9ad8).
Он совпадает с ранее закреплённым. Указание «EML 0.3.2» в исходных данных ТЗ —
смешение с версией EMF: установленный dbghelp.dll точно совпал с release EML 0.2.0.
Исторические отчёты задним числом не переписаны.

| Конфигурация | 1287369 | Доказательства и предел |
|---|---|---|
| EML standalone 0.2.0 | PARTIALLY_SUPPORTED | pinned parser прочитал текущие KFC и EXE; старые локальные логи сообщают type registry loaded; контролируемой writer/load проверки сейчас нет |
| EMF 0.6.18 integrated content | PARTIALLY_SUPPORTED | vendored EML 0.2.0 + пять patches; иная файловая модель и отключённый export |
| Новый самостоятельный EML release | UNKNOWN | после 0.2.0 не найден; нельзя называть 0.3.2 текущей EML |

[Release 0.2.0](https://github.com/Brabb3l/kfc-parser/releases/tag/v0.2.0)
не даёт доказательства всей цепочки source → serializer → writer → game renderer
для нашего patch на новом build. [Issue 37](https://github.com/Brabb3l/kfc-parser/issues/37)
о несовместимости с 1.0 создан до 0.2.0; он не доказывает отказ текущего пакета.
[Issue 43](https://github.com/Brabb3l/kfc-parser/issues/43) описывает Lua reference-stack
panic на большом наборе модов. Это причина не включать лишние моды; локальный тест
одного patch всё равно необходим.

Подтверждённые механизмы в неизменённом upstream:

- [game.version](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game.rs#L16): KFC version string, не Steam build ID.
- [get_resource / get_resources_by_type / create_resource](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets.rs): composite key GUID/type/part; lookup отсутствующего ресурса возвращает nil.
- [mapped reflection](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets/value/mapped.rs): доступ к полю через userdata; HashKey32 читается как `.value`, а не Lua table-only conversion.
- [load.rs](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/load.rs#L249-L337): registry связан с версией и извлекается из EXE.
- [writer.rs](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/kfc-base/src/container/writer.rs): DAT allocation/serialization относятся к writer, не к успешному lookup в памяти.

EMF 0.6.18 несёт **собственную сборку `emf_content.dll`** из EML, с исправлениями
zip/thread lifetime и безопасной записи DAT при hard links:
[EMF_PATCHES.md](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/EMF_PATCHES.md).
Это не бинарно идентичный standalone EML.

Критическое отличие: [content loader](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/engine_parts/content_loader.md#L17-L70)
строит shadow `emf/content/client`, перенаправляет чтение данных игры, **выключает
EML export** и уступает standalone `dbghelp.dll`. `mode=on` не переопределяет конфликт.
Наш patch 0.4.0 выводит evidence через `loader.features.export` / `io.export`;
при shadow loader этого evidence не будет. Нельзя молча засчитать writer log как
подтверждение typed source/clone. До Phase B надо выбрать одного владельца content
и реализовать/проверить соответствующий канал evidence. Сейчас выбор не сделан.
