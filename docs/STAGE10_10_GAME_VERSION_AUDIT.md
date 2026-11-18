# Stage 10.10 — фактическая версия игры

Проверено 2026-11-18, Phase A. Игра и сервер не запускались.

| Идентификатор | Результат |
|---|---|
| Предыдущая конфигурация | 1.0.0.3, internal build 1273043 |
| Установленная игра | 1.0.1.2, internal build **1287369** |
| Последняя найденная публичная версия | 1.0.1.2 / 1287369; официальный hotfix от 2026-11-04 |
| Steam build ID | **26430625** |
| Depot | 1203621 |
| Depot manifest ID | **7226436020230696061** |
| EXE размер | 35 476 040 bytes |
| EXE SHA-256 | `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77` |
| PE FileVersion / ProductVersion | отсутствуют; не использованы как доказательство |
| Встроенная engine version | `0.0.15.0`; это не маркетинговая версия игры |
| Game git | `e4dfdc45cb5d96b452a45df11195a0e56d5bafa3` |
| Update detected | **true** |

Пути: `D:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe` и
`D:\SteamLibrary\steamapps\appmanifest_1203620.acf`. Steam manifest прочитан;
его LastOwner и полный текст не публикуются. Steam build, depot manifest и internal
game build — разные идентификаторы, их нельзя подставлять друг вместо друга.

Build извлечён из EXE через read-only Python
[exe_types.py](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/tools/re/exe_types.py).
EXE не исполнялся. Получены 12 658 reflected types. SHA совпал с
[upstream known-build research](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/ENGINE_MAP.md#L76-L88).
KFC и `.bak` сообщают `1287369|^/game38/branches/release_1.0|2026-11-04T11:17:54.051725Z`.
Совпадение version tag не доказывает чистоту KFC.

Цепочка после 1273043: **1283531 / 1.0.1.0 (2 ноября)** →
**1285601 / 1.0.1.1 (3 ноября)** → **1287369 / 1.0.1.2 (4 ноября)**.
Проверены [официальные новости](https://enshrouded.com/en-US/news),
[Patch 1](https://enshrouded.com/en-US/news/changelog-for-patch-1),
[Hotfix 4](https://enshrouded.com/en-US/news/changelog-for-hotfix-4-v1011) и
[Hotfix 5](https://enshrouded.com/en-US/news/changelog-for-hotfix-5-v1012).
Это результат проверки на указанную дату, а не обещание отсутствия будущих обновлений.
Steam update, verify и downgrade не выполнялись.
