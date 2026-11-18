# Единственный content owner

Официальный latest release повторно проверен GitHub API18 ноября: [EMF v0.6.18](https://github.com/matenm/emf-enshrouded/releases/tag/v0.6.18), опубликован17 ноября22:47:55Z. Исследуется commit`fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`. EML latest — [v0.2.0](https://github.com/Brabb3l/kfc-parser/releases/tag/v0.2.0), commit`16708594d686b030d909f2d835b199d879ea9ad8`. DLL в этой фазе не запускались.

| Критерий | Standalone EML0.2.0 | EMF integrated content |
|---|---|---|
| Оригинальные ресурсы | Writer может менять KFC/resources/DAT в game root | Private KFC/resources в shadow; EXE/base DAT hardlinks read-only по проекту |
| Build1287369 | Reflection из EXE; текущий runtime не проверен | Та же EML reflection, patched vendor; текущий runtime не проверен |
| Установка | dinput8 + dbghelp, отдельные config/log/export | dinput8/core/content/Lua, один owner, shadow lifecycle |
| Rollback | Нужны game-resource backups | Remove attributed loaders/mods; shadow отдельно по manifest, не трогая оригиналы |
| Resource lookup | EML get_resource/get_resources_by_type | Те же API в content build |
| Evidence | Старый export доступен по capability | export=false; print/log + state + shadow readback |
| Поддержка | Brabb3l upstream EML | EMF vendor EML0.2.0 + documented patches |
| Обновления | Отдельная совместимость двух loaders | Один release, но ABI/shadow/source pins всё равно нужны |
| Humanoid | Возможен EML patch; не гарантирует render | Возможен тот же patch API; render UNKNOWN |
| Долгосрочно | Более сложное восстановление game resources | Предпочтительный кандидат при подтверждении evidence и private writes |

**Рекомендация: integrated content, условно; installation_ready=false.** Это архитектурный выбор для Phase D/E, не runtime acceptance. Не включать одновременно два owner. [decide_content](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_owner.h#L58) уступает dbghelp/EML chain даже при mode=on.

Shadow: `<game>/emf/content/client`; server отдельно. [build_shadow](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_shadow.h#L164): real copied mods, private KFC/resources, linked EXE/DAT; cache/index/tmp пересоздаются, новые DAT начиная с base container count. Нельзя считать число55 навсегда фиксированным. Index hardlinks запрещены [Rust build](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/content/src/lib.rs#L277); vendor writer сначала удаляет имя DAT, чтобы не писать через link: [EMF_PATCHES](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/EMF_PATCHES.md).

На пути shadow не допускаются reparse points, нужен поддерживающий hardlinks том. `.bak` heuristic выбора базы не подтверждает чистоту; смешанный root нельзя подавать на build. Нельзя проверять shadow нашим recovery inventory с запретом всех hardlinks: для будущего shadow audit нужна отдельная read-only проверка file identities/link counts.

Порядок: held game entry → выбор owner/base/mods → shadow build → EML run/write → success/unload → shadow.txt/state → redirect → chained DLL/core/runtime → игра. Content DLL не живёт как runtime resource-query service. Сортировка mod output не гарантирует зависимости исполнения; финальный install plan должен включать только наш content patch и проверенные зависимости. [Upstream lifecycle](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/engine_parts/content_loader.md#L88).
