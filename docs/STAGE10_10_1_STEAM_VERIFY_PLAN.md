# Steam Verify — ручная процедура после согласованной очистки

Актуальная контрольная точка: Phase B завершена, backup209/209 и карантин81/81
повторно проверены. [Phase C report](STAGE10_10_1_PHASE_C_REPORT.md).
Дополнительный [список30 файлов и KFC.bak](STAGE10_10_1_RESIDUAL_CLEANUP_APPROVAL.md)
ещё не согласован и не выполнен. **Сейчас Verify не запускать.**

Перед ручным Verify Codex должен подтвердить закрытые игру/server, завершение только
согласованного карантина, его exact journal/SHA, целостность сохранений и доступность
существующего backup. Не выполнять старый rollback; старый Phase B manifest уже не
соответствует текущему inventory и не подлежит повторному запуску.

Ограниченный backup не содержит тела DAT. Он не гарантирует возврат всех DAT к
текущему mixed state после Steam repair. Пользователь принял это ограничение;
новая полная52GB копия не создаётся. Объём скачивания Steam заранее неизвестен.

После отдельного сигнала о готовности выполнить вручную:

1. Открыть Steam → Библиотека → Enshrouded.
2. Открыть Свойства → Установленные файлы.
3. Нажать «Проверить целостность файлов игры».
4. Дождаться полного завершения, записать сообщение Steam о результате.
5. Не запускать игру и dedicated server.
6. Сообщить Codex: «Проверка Steam завершена» и текст результата.

Сообщение пользователя разрешает продолжить read-only post-Steam audit по текущему
ТЗ; новую задачу писать не нужно. Verify не удаляет гарантированно сторонние файлы.
Изменения Steam не принимаются автоматически за правильные.

Далее Codex:

1. Определит EXE/internal/Steam build и depot заново; при новой версии не применит
   прежний профиль или hashes автоматически.
2. Снимет полный inventory и сравнит ADDED/REMOVED/CHANGED/UNCHANGED, LOCAL и остатки;
   отдельно отметит RESIDUAL_MOD_ARTIFACT/UNKNOWN, .bak и DAT set.
3. Повторит Inspector lookup/source/clone/npcId/preset/graph/hierarchy/HashKey32/visual
   audit на восстановленной базе. Ошибка lookup не равна отсутствию clone.
4. Применит clean-baseline evaluator. При недоступности независимых depot hashes
   явно зафиксирует PARTIAL и предложит обоснованный ограниченный acceptance,
   если остальные resource-level доказательства достаточны.
5. После принятия clean baseline создаст отдельный verified clean backup без DAT-тел,
   если original DAT гарантированно вне write scope; продолжит patch/observer/Bridge
   migration и exact install/rollback plan. Установка по-прежнему требует разрешения.

Игра/server/Steam Verify не запускаются Codex; saves не правятся и не восстанавливаются.
