# Movement0.3.4 — подтверждение handoff по последовательным ticks

2026-11-22. **INSTALLED_READY_FOR_MANUAL_START / RUNTIME_UNVERIFIED**.

После разрешения пользователя установлен подготовленный exact7: пять замен и два новых файла. Проверены effective42/42, backup28/28 (LOCAL23 + пять замен), неизменность LOCAL и прежней истории; rollback dry-run PASS. [Installation receipt](../compatibility/experiments/movement_0_3_4/installation/receipt.json). Для крупных DAT использована проверка метаданных с унаследованными хешами, для остальных файлов — свежий SHA-256. Код после офлайн-проверок не менялся, тесты повторно не запускались.

Игра агентом не запускалась; новая сессия ещё не использована. Следующий шаг: пользователь загружает LOCAL Body Test / AI Body Test slot1/1 и сообщает «загрузился», затем одна разрешённая автоматическая сессия0.3.4. Реальный Follow этой версии пока не подтверждён. Ниже сохранены результаты предыдущей сессии и подготовка исправления.

В единственной сессии0.3.3 PID532656, LOCAL Body Test / AI Body Test slot1/1,
type1 снял decision5. Реального Follow не было:0 villager_move,0 probes.
Непосредственно при старте NPC находился в state13/decision5, время6.79797ч;
выход из самой анимации Sleep в этой сессии не наблюдался.

| Время | Наблюдение |
|---|---|
|22:48:39.705|START; override исходных часов20.344039916992188/6.807158946990967|
|22:48:42.021|Единственный WAKE_TYPE1_INTENT на текущую позицию NPC|
|22:48:42.062|Roam7, decision1, walker1 — переход после type1 наблюдается|
|22:48:42.462|Roam7, decision1, walker8/TargetReached, дистанция до цели0.734785м|
|22:48:42.482|Idle3, decision1, walker0 — walker уже сброшен переходом|
|22:48:50.015|WAKE_HANDOFF_TIMEOUT:0.3.3 ошибочно требовал Idle и walker8 одновременно|
|22:48:50.031|SCHEDULE_RESTORED, CLEANUP_COMPLETE без reload|

Runner завершён:10 samples,0 приказов Follow; дистанция до игрока9.12374–12.47083м.
Это не успешное следование. Дополнительный read-only discover подтвердил
отсутствие активного villager_move, status — STOPPED/cleanup=DONE.
Фактическое исполнение type1 согласуется с переходами/достижением цели;
отдельного native command-ID/ACK у emit нет. Дальнейшее движение с decision2
относится к native AI, не к Follow.

До расходования сессии исправлена отдельная ошибка Python: follow_033.py
импортировал receipt/install constants Stage16 вместо install_follow_033.
Одна адресная regression-проверка PASS0.008с, затем ровно один запуск сессии.
Игровой пакет0.3.3 при этом не менялся; повторов wake/Follow не было.

## Минимальная правка

`wake.lua` запоминает только последнее наблюдение Roam7/decision1/TargetReached8
для своей цели и NPC в пределах0.75м. Следующий tick может подтвердить
Idle3/previousState7/decision1/walker0 не позднее1с. Совпадение текущей цели,
идентичность и отсутствие другого приказа проверяются снова. Любое промежуточное
несовпадение сбрасывает наблюдение. Одного Idle/изменения decision недостаточно.
Старый одновременный terminal-критерий также сохранён.

Новые логи дополнительно показывают previous_state и target_matches — в старом
журнале этих полей не было. Проверки цели/previousState не удалены на основании
неполных данных. Ошибка или timeout по-прежнему останавливают Follow и запускают
cleanup; повтор type1 запрещён. Радиусы20/50, алгоритм маршрутов, deadline210с,
Runner205с, лимиты приказов и отложенная отмена не изменены.

36/36 целевых тестов PASS1.071с: последовательность PID532656, Idle без прибытия,
устаревшее/чужое наблюдение, отсутствие overlap, начало Follow после handoff,
ошибка/timeout/cleanup, недействительный world, Lua-host и точный пакет/Runner.
Полный suite не запускался. Тесты моделируют двигатель; новая логика в игре
ещё не проверена, в частности previousState/цель и дистанция≤0.75м.

## Закрытие и следующий запуск

После «закрыл»: SHORT_POST_CLOSE_PASS_SCHEDULE_RESTORED.38 installed-файлов
неизменны,2 runtime-файла — SPENT и ACQUIRED→RELEASED. Backup28/28,
158 прежних runtime/intent файлов и112 spawn-history записей сохранены.
Оригиналы67/shadow77 соответствуют baseline: DAT только по метаданным с
унаследованными SHA, остальные файлы хешированы заново. LOCAL23, content6/
metadata7, добавлений/удалений0; семантика сохранений не проверена. Отката нет.
Подробные данные: `runtime/movement_0_3_3/session532656`.

Пакет `dist/movement_0_3_4`, exact manifest
`compatibility/experiments/movement_0_3_4/exact-update-manifest.json`, SHA
`2c27084a04e0c73859803db1b9ce629ce713690a87ca179154408a5739e851df`.
Exact7: заменить main.lua/mod.json/README.md/follow_config.lua/wake.lua;
добавить follow-movement-0-3-4.lock и schedule-movement-0-3-4.jsonl.
Follow.lua, schedule.lua и остальные игровые файлы не заменяются. Effective42,
будущий backup28=LOCAL23+5; сейчас backup/receipt новой установки не создавались.
Новая сессия и журнал отдельно от0.3.3, вся история сохранена.

`scripts/install_follow_034.py` без флага установки: READ_ONLY_PREFLIGHT_PASS.
Baseline post-close SHA `5a121f64e67d5d048d891572781f413b6c3033054a793a20a63cbffbe9e65f67`.
После отдельного разрешения установить exact7. Затем ручной запуск игры и
«загрузился»; одна отдельно разрешённая сессия через `scripts/follow_034.py`
с актуальным PID и указанным pinned manifest. Сначала подтвердить handoff и
реальное движение, затем повороты/30–40м/>50м/возврат≤20м; целевые180с оценивать
по координатам, не по ACCEPTED. После остановки проверить lease и приказы.
Новая версия не устанавливалась; игра и сервер агентом не запускались.
