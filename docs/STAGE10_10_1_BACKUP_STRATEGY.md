# Две независимые резервные копии

Фактические backups на Phase A **не создавались**. Старые backups1273043 не используются для восстановления ресурсов1287369.

Backup1 `Pre-Cleanup Mixed State`: все non-DAT файлы текущего game inventory, LOCAL23, приватная копия текущего receipt; полный SHA/size inventory всех DAT хранится в исходном плане. Размер данных **419 971 833 bytes** (~400.52 MiB), включая receipt2057 bytes. Карантин81 займёт дополнительно **29 504 495 bytes** (~28.14 MiB). CLI проверяет минимум16 MiB свободного места сверх данных backup и1 MiB сверх карантина; место для manifest/журналов входит в этот запас.

Это ограниченный recovery backup. Полное возвращение mixed state после Steam Verify **не гарантируется**, потому что тела DAT не сохраняются. Verify может заменить любой DAT, включая ранее совпадавший. Полная копия game+LOCAL+receipt потребовала бы **51 924 042 489 bytes** (~48.36 GiB) без запаса. Пользователь ранее отказался от полной копии игры; рекомендован ограниченный вариант с возможностью переустановки через Steam, а не обещание полного rollback.

Наблюдавшееся свободное место: C618068725760, D415327186944 bytes; перед Phase B повторить. Точные объёмы меняются при изменении inventory.

Backup2 `Verified Clean Baseline` создаётся **после** Steam audit. Для integrated content предполагается сохранить clean EXE/KFC/resources, LOCAL, существующие затрагиваемые файлы и новый install plan/receipt; DAT manifest без копирования тел, поскольку новые записи должны идти в private shadow. Нижняя оценка по текущим размерам EXE+KFC+resources+LOCAL — **260 565 889 bytes**, но это не финальный размер чистой базы. Финальный набор/объём зависит от Phase C/D и свежего install plan. Если проверка writer выявит запись в исходный DAT — установка блокируется, стратегия пересматривается до разрешения.

Каждая копия: отдельная новая папка, build/EXE/Steam/depot identity, UTC timestamp, исходные и backup paths, SHA/size, manifest, verified reread. Неполная копия не получает валидный завершающий manifest. Restore policy: только точный reviewed path/build; отсутствие auto-restore; saves восстанавливаются отдельно по согласию. `full_mixed_state_restore=false` сохраняется явно.

Приватный receipt копируется в backup как `install-receipt.json`; токен не публикуется. При подготовке Phase B сверить отдельно SHA manifest и запретить вложенные/пересекающиеся backup/quarantine/game roots.
