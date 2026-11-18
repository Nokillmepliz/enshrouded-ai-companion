# Точный cleanup manifest

[Machine-readable manifest](../compatibility/recovery/1287369/cleanup_manifest.json) содержит все 272 файла, абсолютные/относительные пути, SHA-256, size, owner, attribution, purpose, action, backup/restore policy и confidence. Он фиксирует наблюдение, а не разрешает операцию.

| Действие | Файлов | Значение |
|---|---:|---|
| QUARANTINE | 81 | Exact hash match с официальным manual0.3.2, receipt10.7 или исходниками AIC |
| STEAM_REPAIR | 57 | KFC/resources и DAT000–054; только Steam, наш инструмент их не удаляет |
| MANUAL_REVIEW | 51 | Недостаточно доказательств для удаления/перемещения |
| KEEP | 83 | LOCAL23, EXE, исторические game logs; KEEP не утверждает официальное происхождение |

81 кандидата включают `dinput8.dll`, старый `emf_core.dll`, Lua host, bundled mods, `dbghelp.dll`, patch0.4.0 и observer. Проверены все девять `applied[]` текущего receipt. Receipt1273043 используется только как свидетельство происхождения, не как разрешение rollback нового build.

Неизвестные/неполностью атрибутированные: `.cache/*`, изменённые конфигурации EMF, loader/core logs, `chain_status.txt`, `installed.txt`, установленный `aic_body/body.lua` (не совпадает с текущим source), KFC.bak, DAT055–063, `enshrouded_local.json`, старый export, EML logs, три vendor/game DLL. Имена/расположение не доказывают owner. Их полный список и хеши — в JSON; никакие из них не удаляются.

DAT055–063 вновь имеют size0 и SHA пустого содержимого, совпадают с прежней инвентаризацией. Это недостаточно для атрибуции: новый depot мог использовать те же номера. Они остаются `MANUAL_REVIEW`; инструмент дополнительно запрещает QUARANTINE для любого `.dat`, `.kfc`, `.kfc_resources`, `.kfc.bak`, EXE и save-root даже при изменённом manifest.

Карантин располагается вне игры и backup, предпочтительно `C:\Enshrouded-ai-companion\runtime\quarantine\<new-id>`. Между дисками используется copy → SHA/size verify → durable journal → повторная live-проверка → unlink ровно одного файла. Директории не удаляются. Existing destination, reparse/junction/symlink/hardlink, новые файлы, hash/build/receipt mismatch вызывают отказ.

Оставшиеся файлы в `emf`/`mods` не разрешают удаление этих директорий целиком. После карантина и Steam Verify они проходят отдельную оценку; обнаружение старого clone или loader блокирует baseline.
