# Steam Verify — будущая ручная процедура

Сейчас Verify не запускался. Не начинать его до Phase B и проверки неизвестных residue.

1. Закрыть Enshrouded и dedicated server. Остановить текущие Steam downloads/Verify.
2. Повторить inventory, build/EXE/Steam identity, receipt hash; сравнить reviewed plan. Любое отличие требует нового review.
3. После отдельного разрешения создать Backup1 и проверить все SHA/size, включая LOCAL и receipt.
4. Перенести только согласованные QUARANTINE81. Не удалять DAT по номеру. Проверить отсутствие старых loaders и конфликтующих chains. `MANUAL_REVIEW` оставить; разрешение на них не предполагается.
5. Пользователь вручную: Steam → Библиотека → Enshrouded → Свойства → Установленные файлы → Проверить целостность файлов игры. Дождаться полного завершения; игру не запускать.
6. Сообщить Codex о завершении. Повторно собрать inventory и сравнить с pre-cleanup и quarantine journal.
7. Проверить EXE/build/depot, весь DAT-набор (включая появившиеся/исчезнувшие номера), KFC/resources, leftovers, loaders, старые patch/observer и LOCAL SHA/size.
8. Read-only Inspector на новой базе: source hunter/blacksmith, отсутствие clone `a1c90001-5e4d-4a91-8a1c-000000000001`, отсутствие npcId2939921867 collision, полный ResourceRegistration/CharacterSetup/visual audit. Ошибку lookup отличать от подтверждённого отсутствия.
9. Запустить clean-baseline evaluator. Сообщение Steam «успешно» не удаляет сторонние файлы и само по себе не даёт CONFIRMED. Без независимых depot hashes максимум PARTIAL.

Безопасные команды в проекте (ни одна не запускает игру):

```powershell
$plan = 'compatibility/recovery/1287369/cleanup_manifest.json'
$planHash = (Get-FileHash -LiteralPath $plan -Algorithm SHA256).Hash.ToLowerInvariant()
.\.tools\python\python.exe scripts/stage10_10_1_recovery.py dry-run --plan $plan --plan-sha256 $planHash
```

Это свежий hash для review, не независимое доказательство доверия. В Phase B сверить его с согласованным commit. Future `backup`/`quarantine` также dry-run без `--execute`; выполнение требует соответствующего `--authorization PHASE_B_BACKUP` или `PHASE_B_QUARANTINE`, нового destination и для карантина `--backup`. Не запускать эти операции сейчас.

После Verify вызвать `stage10_10_1_inventory.py after --run-dir runtime/stage10_10_1_post_steam_<new-id>` в новой согласованной сессии: существующий output не перезаписывается. Разрешён только project runtime output; reparse paths запрещены. Для текущей Phase A after используется только для доказательства отсутствия изменений; не подменять им будущий Phase C audit.
