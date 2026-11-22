# Movement 0.3.5 — реакция на движение игрока

2026-11-22. **PREPARED_RESPONSIVENESS_ONLY_HOME_LIMIT_UNRESOLVED**. В игре остаётся0.3.4. Новая версия не устанавливалась; новый игровой тест не разрешён и не выполнялся.

Короткий post-close аудит PID536832 прошёл:40 неизменяемых установленных файлов,28 backup-файлов,191 прежний runtime/intent файл и112 spawn-history записей проверены. Два изменившихся runtime-файла соответствуют SPENT и ACQUIRED→RELEASED. Расписание восстановлено, после Follow активного приказа не было. Оригиналы67/shadow77 совпадают с baseline: для больших DAT — метаданные с унаследованными SHA, для остальных файлов — свежие SHA-256. LOCAL23:7 изменившихся содержимых,8 метаданных, без добавлений/удалений; имена тестовых персонажа/мира сохранены. Семантическая целостность saves не доказана. [Результат аудита](../compatibility/experiments/movement_0_3_4/post-close-536832.json).

В0.3.5 изменено:

- Retarget при смещении игрока больше3 м и интервале не меньше2 с вместо8 м/8 с. Отсчёт смещения идёт от позиции игрока, использованной при запросе цели, а не от более поздней позиции при отправке приказа.
- Интервал отправки уменьшен4→1 с; после отказа кандидата остаётся задержка4 с, чтобы не расходовать бюджет быстрыми бесполезными повторами. Параллельных приказов нет: отмена в свежем server tick, подтверждение в следующем tick, затем новый приказ.
- Использован существующий native hold5 с после прибытия. При удалении игрока за2,8 м удержание снимается тем же механизмом отмены. Постоянного выключения native roaming или записи в saved нет.
- Read-only команда `aic_companion_movement.nav_info` возвращает home, template radius, saved override/radius, effective radius и native leash. Python записывает их перед единственным start. Дублирующийся NPC/неподтверждённые поля запрещают эту проверку, без записи компонентов.

Сохранены20/50 X/Z,3D proximity, native Ground/Path/villager_move, ограничения высоты не добавлены; исправления wake/cancel/cleanup сохранены. Лимиты210/205 с,24 попытки приказа,30 probes,2 recoveries и heartbeat4 с прежние. При частых поворотах бюджет может закончиться раньше205 с: длительность Runner не доказывает180 с устойчивого Follow.

94/94 целевых теста PASS,1,250 с: responsive/readonly navigation, lifecycle инвалидированного world, wake, реальный Lua host, Follow и пакет. Первые прогоны выявили ошибки новых fixtures и пропущенный allowlist версии Python; исправлены. Полный suite не повторялся. Офлайн-проверки не доказывают улучшение поведения в игре.

Пакет `dist/movement_0_3_5`, manifest [exact-update-manifest.json](../compatibility/experiments/movement_0_3_5/exact-update-manifest.json), SHA-256 `5e8c73e36a8a5a8cb422517f5704ac2d3b58203a92617fc19aa8d5630c96472c`. Exact8: шесть замен(main,controller,follow,config,mod,README) и два новых lock/journal; effective44. Предусмотрен backup29=LOCAL23+6 замен, пока не создавался. `install_follow_035.py` без флага установки: READ_ONLY_PREFLIGHT_PASS. Проверен актуальный post-close baseline SHA `02850eb4f979f14874b0bfa5dfb64f4b59ca4426906b962e0a3b3b3bec2f0029`. Истории0.3.4 и более старых сессий закреплены; новая сессия имеет отдельные token/lock/журнал.

Оставшийся блокер свободного Follow — домашний радиус:

- [EMF villager_moves.cpp:145](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp#L145) выбирает `saved.roamingRange`, если включён override, иначе `template.roamingSetup.maxRadiusFromSpawn`; отдельно проверяет leash от дома. Шесть runtime-отказов0.3.4 прямо указывают на effective10 м.
- Существующий локальный read-only экспорт `runtime/research/stage10_5/hunter_assistant.json` содержит template radius10, targetRadius8, bedRadius50. Это исторический ресурсный экспорт, не свежий readback существующего NPC в build1287369; происхождение effective10 только из template не доказано.
- [world:template read-only](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/lua_host/bindings.cpp#L227) запрещает runtime-запись шаблона; изменение saved override нарушило бы текущий запрет на saved-поля. Обход проверки EMF не решает ограничение штатного AI и опасность native возврата домой.
- Допустимое направление — изменение только нашего clone через существующий integrated content patch, с неизменным GUID/npcId, контролем source integrity и readback effective radius. Если есть сохранённый override, изменение template само по себе недостаточно. Простое увеличение радиуса также расширяет native wandering и не делает домашнюю точку подвижной; бесконечный радиус или произвольные записи не предлагаются.

Поэтому content patch, evidence/fingerprint и установленный humanoid template в этой итерации не менялись. Пакет0.3.5 исправляет задержку и предоставляет точные параметры для следующего решения, но **не готовое устранение домашнего ограничения**. Для следующего разрешённого запуска сначала прочитать nav_info; не расходовать новую Follow-сессию в расчёте на уже исправленный home. Новую установку, запуск сессии и изменение content согласовывать отдельно. Spawn_ready=false.
