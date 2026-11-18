# Stage 10.10.1 Phase F — load-only validation

## Checkpoint до ручного запуска, 2026-11-18

**READY_FOR_MANUAL_START**. Phase F явно разрешена пользователем. Runtime тест
ещё не выполнен; итогового load-only verdict пока нет.

Fresh preflight завершён в `2026-11-18T12:29:31.689254+00:00`:

- Build1287369 / Steam26430625 / depot7226436020230696061, Steam idle, game/server закрыты.
- Pinned approved plan/profile/package/binding и настоящий Phase E receipt PASS.
  Installed16/16 SHA/size PASS; clean backup27/27 PASS.
- 137 исходных файлов и23 LOCAL совпали с baseline по SHA/размеру/mtime.
  Полный game inventory153=137+16; конфликтов, неизвестных файлов, reparse points,
  предварительных hardlinks и shadow не обнаружено.
- Сохранён новый snapshot67 оригинальных ресурсов: EXE,KFC,resources,64 DAT,
  с SHA/size/mtime/volume/file ID/link count. Полные153 game/23 LOCAL сохранены отдельно.
- Rollback dry-run по настоящему receipt PASS16; никаких операций отката не выполнено.
  Content input fingerprint совпал с Phase E; это metadata-cache identity,
  а не подтверждение выполненного writer.

LOCAL `default/character0.ksd` и `default/world0.ksd` совпадают с принятым backup
по SHA; в них найдены соответствующие имена Body Test / AI Body Test (по одному
UTF-8 вхождению). Привязка slot1 опирается также на предыдущую runtime-проверку
Stage10.7. Это offline соответствие сохранённых файлов, не декодирование всей
KSD-схемы и не доказательство выбранного сейчас runtime slot. После ручной загрузки
обязательна свежая проверка Bridge character.storage/name/slot и world.name/slot.
Совместимость загрузки прежних saves с новым build пока не установлена; возможные
изменения saves самой игрой будут отдельно зафиксированы, без восстановления.

Private evidence:
`runtime/stage10_10_1_phase_f/20261118T122931689254Z`:
`originals-before.json`, `inventory-before.json`, `rollback-before.json`, `preflight.json`.
[Публичный preflight](../compatibility/migration/1287369/phase_f/preflight.json).
Read-only script: [preflight_phase_f.py](../scripts/preflight_phase_f.py).
Python syntax/compile PASS; реальный preflight exit0. Полный unit suite повторно
не запускался: существующие validators неизменны, новый orchestration script
проверен фактическим read-only выполнением. Исторический691-test результат Phase E
не выдаётся за новый запуск suite.

Следующий checkpoint: пользователь вручную запускает Enshrouded через Steam,
выбирает LOCAL Body Test (slot1) и LOCAL AI Body Test (slot1), сообщает «загрузился».
Codex проверяет только EMF/Bridge/observer/evidencev8, writer/state/shadow/readback/
resource redirection согласно [плану](STAGE10_10_1_LOAD_ONLY_PLAN.md).
При ошибке запуска или отсутствии нужного LOCAL выбора не создавать замену
и не продолжать эксперимент: сохранить сообщение ошибки для диагностики.
Игра закрывается пользователем после runtime capture; затем отдельный post-run audit.

Spawn/despawn, entity/faction/inventory mutations и automatic rollback запрещены.
`runtime_validation=WAITING_FOR_MANUAL_START`, `spawn_ready=false`.
