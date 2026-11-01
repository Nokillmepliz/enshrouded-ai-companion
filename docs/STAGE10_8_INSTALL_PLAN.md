# Stage 10.8 — будущий install/recovery plan

Статус: **BLOCKED — НЕ ВЫПОЛНЯТЬ**.

Текущее состояние после Stage 10.7: patch 0.4.0 установлен; EML изменил KFC/resources; созданы DAT 055–063; LOCAL saves штатно изменены; receipt содержит 9 файлов; rollback готов и не выполнялся. Runtime scaffold Stage 10.8 не установлен.

Перед любой будущей Phase B требуется отдельное разрешение и закрытие research blockers. План:

1. Убедиться, что игра/server закрыты.
2. Проверить текущий receipt 9/9 и Stage 10.7 post-run attribution.
3. Не откатывать Stage 10.7 автоматически.
4. Создать новый verified backup текущих KFC/resources и полного LOCAL-набора; проверить каждую копию.
5. Сформировать новый install plan с новым run token; не переиспользовать Stage 10.7 token.
6. Установить только reviewed runtime controller, сохранив observer read-only и запрет autospawn.
7. Проверить hashes, версии, namespace, disabled defaults, отсутствие иных модов и rollback dry-run.
8. Остановиться до отдельной Phase C.

Recovery после будущего spawn требует отдельного разрешения: сохранить неудачное состояние, затем восстановить весь согласованный LOCAL-набор из нового pre-spawn backup и проверить hashes. Не удалять entity по широкому фильтру и не редактировать saves вручную.

Сейчас установка, backup, rollback и изменения игры не выполнялись.
