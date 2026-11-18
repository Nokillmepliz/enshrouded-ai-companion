# Stage 10.11.2 — ручной Local Interactive Spawn, PID249976

2026-11-18. Итог `POST_CLOSE_INTEGRITY_PASS_SPAWN_NOT_EXECUTED`; runtime blocker `GROUND_UNCONFIRMED_EXACT_SUBCONDITION_UNKNOWN`.

Свежий closed preflight16:17:19–16:17:51UTC прошёл: installed23, backup23, обе истории45, UNUSED latch, полный baseline244game/23LOCAL. Пользователь самостоятельно запустил игру19:18:15 местного времени. Read-only hello/state и continuation status подтвердили LOCAL Body Test / AI Body Test slot1/1, EMF0.6.18/API46/build1287369, новую session, NEW и здоровье100/100. Затем пользователь самостоятельно запустил выданную PowerShell-команду.

## Результат попытки

- Один probe: GROUND_REQUESTED19:21:16.009 → STOPPED ground_unconfirmed19:21:20.403,4.394s. Это отказ проверки ground, не deadline timeout. Клиент корректно сообщил `CONTROLLER_REFUSED:ground_unconfirmed` и прекратил работу.
- READY/Path-ready, ready-window и local-confirmation отсутствуют. Подтверждение Y, фактическое создание, визуальная проверка NPC и наблюдение30–60s не состоялись. Работу локальной клавиши Y в реальной игре этот запуск не подтверждает.
- В журнале0 spawn-request, общий durable spawn-intent отсутствует, latch UNUSED. Полный core log не содержит вызова aic_first_spawn.spawn, SPAWN_ATTEMPT или ENTITY_ID_RETURNED. Проверена связь отказа с nonce/session текущего probe; предыдущие45 файлов истории неизменны.
- ground_unconfirmed объединяет несколько условий: ground query не подтвердил результат, невалидные координаты/отклонениеX/Z, перепад высоты>0.75m, fog не none/removed, наличие water. Значения callback в текущем установленном контроллере не записываются. Конкретное условие неизвестно; утверждать, что виноват склон или вода, нельзя.
- После ошибки новых игровых команд не отправляли. Пользователю сообщено не повторять команду; затем он вручную закрыл игру. Установленный Lua и safety gates не менялись; журнал/latch не сбрасывались.

## Post-close audit

Новый read-only `scripts/audit_stage10_11_2_closed.py` использовал реальное время текущей сессии и pinned baseline SHA `6cd6ac15025cce3119236b1e52d998a5d850e86c95ec6eace16c1af70e9d23bf`. Повторно применены существующие install/backup/snapshot/post_close_v2 валидаторы.

- Игра/сервер закрыты. Originals67/67 и shadow77/77 точно совпали по SHA/size/identity/mtime/links. Installed23 и backup23 проверены. Старый install backup также проверен штатным gate.
- Единственный добавленный245-й игровой файл — точный rename прошлого лога в `backup/enshrouded_2026-11-18T19-18-15.log`. Изменены четыре текущих лога и mtime пустого chain_status с прежней identity. Неатрибутированных изменений нет.
- LOCAL23 без добавлений/удалений, пустых файлов/новых hardlinks; имена Body Test / AI Body Test сохранены. Content изменился у7 файлов, metadata у8, включая основные character/world, резервные копии и local_settings. В логе10 world-save событий. Семантическая целостность saves не установлена; восстановления не было.
- Новый snapshot SHA `283893ac38d72220b10af73e9a131d269000031de0259b263d9bef84674daf19`. Старый baseline/backup/plan не переписывались.

Публичные preflight/context/refusal/post-close JSON находятся в `compatibility/experiments/stage10_11_2/`. Private evidence: `runtime/stage10_11_2/live/20261118T161719780155Z/session249976/post-close/`. Сырые логи содержат private binding и не публикуются.

Повторно выполнены29 tests runtime_validation:29PASS,0failures,0.003s,exit0. Py_compile/diff check PASS. Полный suite885 офлайн-этапа здесь повторно не запускался.

## Дальше

Другое открытое ровное сухое место может пройти проверку, но это не доказанное исправление неизвестного условия. Новый эксперимент требует отдельного continuation plan с сохранением всех трёх probe-историй, актуального baseline/backup и отдельного согласования. Текущую команду повторять нельзя. Новую попытку, reset, destroy, rollback или изменение модов агент не выполнял.

`spawn_ready=false`, `production_spawn_ready=false`, `render=UNKNOWN`. Эксперимент завершён.
