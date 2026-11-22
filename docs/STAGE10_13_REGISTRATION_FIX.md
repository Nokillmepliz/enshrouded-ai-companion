# Stage10.13 — исправление регистрации и проверяемое продолжение

Movement0.2.1 исправляет только интерфейс команд, алгоритм Follow не меняется.

**Установлено 2026-11-22:** closed preflight PASS, backup26/26 (644217байт),
exact3/3 и effective31/31 hashes PASS. Остальные255 игровых файлов и LOCAL23
неизменны;112 записей истории/старые intent/SPENT сохранены. Прежний journal
сохранён побайтно; follow-session.lock остаётся UNUSED и не заменялся.
Runner preflight и rollback dry-run PASS, откат/движение не выполнялись.
[Receipt](../compatibility/experiments/stage10_13/registration-fix/installation/receipt.json).
Backup: `runtime/backups/stage10_13-movement_0_2_1`, manifest SHA-256
`ea332f1eec7f88f7bb60d49055607126f8fdca040845bbeefcacfdbeec4aff00`.
Новый pre-runtime baseline:
`runtime/stage10_13/registration-fix-installation/inventory-after.json`, SHA-256
`a67f92b091f533c807d43d6b2b984b389dcd67ecdabbb377d1992d2ce6b3a175`.
Ожидание «загрузился»; игру запускает только пользователь.

| Полное имя EMF | Длина |
|---|---:|
| aic_companion_movement.f_start | 29 |
| aic_companion_movement.f_step | 28 |
| aic_companion_movement.f_stop | 28 |
| aic_companion_movement.f_status | 30 |

Lua проверяет длину до регистрации и результат `emf.command`. Отказ завершает
загрузку с ошибкой; валидатор Python не принимает неработающий мод. Python
использует те же короткие имена и требует версию0.2.1.
Регрессионный host-тест загружает настоящий main.lua, сравнивает все семь
зарегистрированных команд с клиентом, проверяет полные имена и32символа.
Mock теперь отвергает длинное имя; возвращение старого follow_start ломает тест.

## Прежний журнал не сбрасывается

Аудит PID471028 доказал: follow_start не зарегистрирован, Follow не начался,
команд движения0, follow-session.lock остался UNUSED. Аудит закреплён SHA-256
`0f6e5855bb644f25af96de7e2d4d994e311e423d16e30ca48e6f913c55851e34`.
Старый `runtime/stage10_13/test-session.jsonl` закреплён SHA-256
`9c394226b46a4698058c549a2310ab17b7a892d5c41e5256488e50a01fcc76d4`.

По отдельному разрешению пользователя следующий Runner открывает **тот же**
журнал без truncate, захватывает файловую блокировку, проверяет старые байты и
дописывает AUDITED_CONTINUATION с доказательством перед новым SESSION_INTENT.
Ничего не удаляется и не переименовывается; новые имена journal/intent не создаются.
После первой дописи исходный hash уже не совпадает: повтор невозможен.
Проверка UNUSED Lua lock остаётся независимой; этот файл не входит в обновление.
После нового start Lua сам потребит UNUSED→SPENT обычным механизмом.

Неизвестный результат новой попытки не разрешает ещё одно продолжение. Новый
каталог или новые token/latch для обхода отказа не предусмотрены.

## Пакет

`dist/stage10_13_movement_0_2_1`: ровно3 замены main.lua/mod.json/README.md.
`follow.lua`, config(native), follow-session.lock, Spawn Controller/SPENT,
observer/content и прежние intent остаются без изменений.
[Exact manifest](../compatibility/experiments/stage10_13/registration-fix/exact-update-manifest.json)
SHA-256 `500d8b6bf9b73cb449d80b444f9b0d59d02e379178cc3aec04823f84c04ed918`.

Backup: LOCAL23+3 заменяемых файла. Preflight сравнивает актуальный post-close
baseline PID471028 и всю прежнюю историю. Установщик журналирует замены и
останавливается при ошибке, без автоматического rollback.

Целевые tests.test_companion_follow + tests.test_companion_movement:
71/71 PASS,0.160с. Дополнительно проверены exact3 и запрет включения lock в
список замен. Полный suite не повторялся. Append-тесты подтверждают сохранение
старого префикса, отказ при изменённом журнале и невозможность повторной дописи.

После установки ждать «загрузился». Разрешение одной сессии уже дано, MOVE не
требуется. Codex проверяет PID/LOCAL/Bridge и запускает:

```powershell
& 'C:\Enshrouded-ai-companion\.tools\python\python.exe' 'C:\Enshrouded-ai-companion\scripts\companion_follow.py' --pid <PID> --manifest-sha256 500d8b6bf9b73cb449d80b444f9b0d59d02e379178cc3aec04823f84c04ed918 --authorized-session
```

Лимиты и native roaming не меняются:180с,24 orders,30 probes,2 recovery.
Реальное следование ещё не проверено. После «закрыл» нужен новый короткий аудит;
прежний journal сравнивать как неизменный префикс, а не требовать неизменности
всего файла после разрешённой дописи. `spawn_ready=false`.
