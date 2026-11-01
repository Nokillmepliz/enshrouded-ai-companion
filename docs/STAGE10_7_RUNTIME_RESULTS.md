# Stage 10.7 — runtime results

**NOT_EXECUTED**

Phase A не запускала Enshrouded, не устанавливала patch 0.4.0, не выполняла rollback и не создавала entity. Поэтому runtime source/clone HashKey32 equality, writer/reload loadability, A/H/R/V/B/C и отображение NPC не подтверждены. Исторический Stage 10.6 результат остаётся `FAILED — V:CHARACTER_SETUP`.

Read-only повторная integrity-проверка текущей установки 0.3.0: игра/server закрыты; backup 24/24 verified; installed files 9/9 match receipt; исходные DAT 55/55 без изменений, ожидаемые DAT 055–063 присутствуют; KFC/resources изменены EML, `.bak` совпадает baseline; LOCAL changed 6, added/removed 0; unknown changes 0; rollback ready; rollback не выполнялся. `spawn_ready=false`.
