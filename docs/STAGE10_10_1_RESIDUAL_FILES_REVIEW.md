# Phase B — проверка оставшихся 51 файла

2026-11-18. Все записи исходного `MANUAL_REVIEW` **оставлены без изменений**. Дополнительная атрибуция не расширяет разрешённый карантин81 и не изменяет reviewed manifest. Пофайловые SHA/size, наблюдения, категория риска и дальнейшая проверка: [residual-review.json](../compatibility/recovery/1287369/phase_b/residual-review.json).

Проверялись реальные оставшиеся файлы: структура JSON/INI, заголовки KFC, совпадение Lua с историей Git, подписи/версионные метаданные DLL. Lua/DLL не выполнялись. Содержимое logs/export, приватный run token и пользовательские настройки не публикуются целиком.

| Остаток | Количество | Результат и влияние |
|---|---:|---|
| `enshrouded.kfc.bak` | 1 | Существенный blocker content baseline: происхождение чистой базы не доказано; влияет на выбор integrated content base |
| DAT055–063 | 9 | Пустые, но текущий KFC содержит64 container entries; владение по номеру/нулевому размеру не доказано |
| `emf/mods/aic_body/body.lua` | 1 | Точное byte-for-byte совпадение с commit026cd8a; старый код, сейчас без loader/main/mod.json, не включать в новую установку |
| `emf/config/*.ini` и `emf/emf_core.ini` | 23 | Старые настройки, включая enabled1 у aic_body/Lua и debug bridge1; сейчас неактивны без загрузчика, опасны при слепом наследовании |
| `.cache/*` | 4 | Generated reflection/cache; нельзя использовать как доказательство clean baseline или переносить в новый shadow cache |
| `export/aic_eml_humanoid/template_evidence_v4.txt` | 1 | Исторический evidencev4, непригоден для новой сессии/receipt/writer acceptance |
| `emf/installed.txt` | 1 | Старый ownership catalog69 строк; manager использует его для классификации файлов, это не актуальный install receipt |
| NVIDIA/Valve DLL | 3 | Authenticode Valid у всех трёх; не подтверждённые mod artifacts, оставить для Steam/depot сверки |
| `enshrouded_local.json` | 1 | Graphics/sound/version settings; не найдено основания считать loader или причиной resource corruption |
| EMF/EML logs и `chain_status.txt` | 7 | Исторические диагностические данные; не startup-конфигурация, не свежие runtime evidence |

Всего51. Отсутствие активного loader после карантина не делает resource database чистой.

## KFC и `.bak`: конкретный риск

Оба заголовка — KFC4, size9396224, version `1287369|^/game38/branches/release_1.0|2026-11-04T11:17:54.051725Z`. У `enshrouded.kfc`64 контейнера, у `.bak`55. SHA отличаются. По [choose_base](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_base.h#L44) integrated loader **выбрал бы `.bak`** при этих входных данных. Это вывод из алгоритма, не выполненный запуск.

В `.bak` не доказано отсутствие clone/необъяснённых изменений. Версия и контейнеры не являются доказательством чистоты. После отдельно разрешённого Steam Verify заново проверить current KFC/resources, DAT-set и наличие clone/npcId через Inspector; `.bak` тоже требует review, а не автоматического восстановления/удаления. Прежний Stage10.10 resource audit обнаружил clone в текущем KFC; его hash после Phase B не изменился, поэтому карантин загрузчиков сам этот blocker не устранил. Повторное декодирование64 resources здесь не выполнялось.

Заголовок читается по подтверждённому [kfc_header.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/kfc_header.h#L3). Значение64 не устанавливает, что каждый из пустых DAT содержит нужные ресурсы: требуется анализ ссылок и официальный depot inventory. Все64 DAT сохранены.

## Старые настройки, код и диагностика

`body.lua` совпадает с [историческим AIC source026cd8a](https://github.com/Nokillmepliz/enshrouded-ai-companion/blob/026cd8a25fac49ce1dbcb1703fa332369c501e9c/mods/aic_body/body.lua). Новая атрибуция объясняет отличие от текущей версии репозитория, но не даёт разрешения переместить этот82-й файл.

Сохранились `aic_body.enabled=1`, `lua.enabled=1`; остальные20 оставшихся mod configs имеют enabled0. Core config содержит `[debug] bridge=1, bridge_verbose=1`. Новая установка должна иметь явный config plan, исключающий старый adapter; перенос старых папок/config целиком недопустим. Конфигурация observer из прежнего receipt вошла в81 карантинных файлов.

`installed.txt` —69 путей, созданных старым installer, а не hash/ownership proof новой установки. Его [читает manager](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/app/install.cpp#L126); не использовать для автоматического ремонта/удаления. Пустой `chain_status.txt` — [выход loader](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/chain_load.h#L2), не chain configuration.

`.cache/types.json` содержит version1287369 и12658 types; `.cache/files.json` содержит cache build_id1792191177401 и72 entries. Cache build_id — значение cache metadata, не Steam/internal game build. Эти файлы не являются независимой проверкой ресурсов. Integrated content использует собственный shadow cache и [пересоздаёт его при build](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_shadow.h#L200); root cache туда копировать не следует.

Старые logs/export можно хранить как историю, но не включать в новый acceptance capture. Отдельно сохранились59 исторических game-log файлов из группы KEEP, также без изменений; они не входят в эти51 MANUAL_REVIEW.

## Подписи DLL

| Файл | Наблюдавшаяся подпись | Версия из файла |
|---|---|---|
| GFSDK_Aftermath_Lib.x64.dll | Valid, NVIDIA Corporation | 2.26.0.0 |
| nvngx_dlss.dll | Valid, NVIDIA Corporation | 310,9,1,0 |
| steam_api64.dll | Valid, Valve Corp. | 10.87.46.89 |

Подпись подтверждает подписанный файл в результате текущей Windows-проверки, а не соответствие конкретному depot manifest. Эти файлы не следует удалять как неизвестные mod loaders. Отсутствие официального per-file сравнения оставляет происхождение точной игровой версии неполностью подтверждённым.

## Решение

Приоритет следующего согласования: восстановление/сверка оригинальных KFC/resources/DAT и оценка `.bak`; затем явный план работы со старыми configs/cache/catalog/code/evidence. Инертные логи и пользовательские настройки сами по себе не являются причиной удалять файлы ради «чистоты».

EMF integrated content принят пользователем как будущая архитектура **при условии** проверки оригиналов и shadow resources. Его установка, Steam Verify и любые дополнительные перемещения не выполнялись; Phase C требует отдельного согласования.
