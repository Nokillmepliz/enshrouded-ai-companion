# Stage 10.15 — отключение окна сна, Movement 0.3.1

2026-11-22. **PREPARED_NOT_INSTALLED / RUNTIME_UNVERIFIED**.
Предыдущий блокер из STAGE10_15.md снят статическим разбором установленного EXE.
Реализован временный per-NPC override; результат «спутник действительно проснулся
и пошёл ночью» ещё требует игрового испытания. Игра не запускалась, обновление
не устанавливалось. Ранее установлен Movement 0.3.0.

## Подтверждение для 1287369

EXE SHA-256 `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77`
совпал с последним post-close baseline и остался прежним после чтения.
Использованы локальные PE helpers EMF и objdump; EXE/DLL не выполнялись.
Хеши диапазонов кода, включая chained unwind parts, сохранены в
`compatibility/experiments/stage10_15/build1287369-sleep-evidence.json`.
Адреса ниже — предпочтительные VA из PE для воспроизведения анализа, **не адреса
для записи или вызова в моде**. ASLR/runtime pointers мод не использует.

| Механизм 1287369 | Проверенные инструкции и смысл |
|---|---|
| Sleep-window `0x14044f690` | +0x50/+0x54 NpcCommon, float hours × double 3600000000000; signed сравнение `tod >= sleep OR tod <= wake` в 0x14044f6c9–0x14044f6ec |
| ShouldSleep `0x140453160` | Idle/DecideTask/Roam и GoToTarget не для сна; вызов окна в 0x140453278; ветвь StayAwakeUntilEvening сравнивает время со sleepTime |
| DecideTask `0x1404631a0` | вызов ShouldSleep в 0x1404631f6; true → decision5 и SetState(FindBed=2) |
| CheckInterrupts `0x140452970` | вызов ShouldSleep в 0x140452cff; также прямое использование окна в 0x140452c3d |
| Sleep `0x140465520` | updateType1 вызывает то же окно в 0x1404656fd; false → StayAwakeUntilEvening и NextState(0), без прямой подмены state |
| Sleep enter | updateType0 → ветвь 0x140465a43, Actor flag 0x800 в 0x140465a89; мод эту запись не подменяет |
| Sleep exit | updateType2 выбирает часы из template +0xa8/+0xb0, записывает +0x50/+0x54 в 0x140465605/0x140465659 |
| SetState `0x14045b320` | old exit(2), штатный сброс walker и смена состояния с enter |
| Commands `0x1404565f0` | type1 → SetState(Roam=7), decision1, target position; type0 — reset. Наш патч новых событий не отправляет |

Сигнатуры Sleep/DecideTask/SetState/Commands/CheckInterrupts дали по одному
совпадению. Назначение установлено по операциям и связям вызовов, не только
по совпадению сигнатуры или версии. Локальный disassembly остаётся в runtime.

Первичные источники уже имелись локально, commit
`fa6efdac2d93dd1d8ac6fe0e2a658140aec35241`:

- [SDK NpcCommon](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/generated/components.hpp#L16150): имена и смещения.
- [Lua world:get](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/lua.md#L880): checked float setter и callback lifetime; world:template read-only.
- [Time of day](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/reference.md#L355): 0≤h<24. Текущий getter 0x140e8f040 читает Daytime+0x48 — источник sleep predicate. Runtime проверяет часы перед применением/поддержанием override.
- [Native executor](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp#L261): Sleep/WantsToSleep pause, повтор собственных приказов и независимые home/leash/busy ограничения.

## Реализация

`schedule.lua` временно задаёт **sleepTime=25, wakeUpTime=−1** только уникальному
спутнику после LOCAL/session/entity/profile gates и расходования нового latch.
Это конечные float-часы на один час за границами суток: оба сравнения ложны на
всём диапазоне 0–24 включительно. Они выведены из проверенного предиката.
Равные часы/нули отвергнуты: такое окно может означать сон весь день.

Если NPC спит, патч ждёт штатного выхода до 15 секунд, не пишет state/decision,
не отправляет Reset, не двигает NPC для пробуждения. На каждом server tick
проверяется lease. Одно наблюдаемое Sleep→другое состояние с повторным выбором
обоих часов допускает однократное повторное применение. Неизвестная запись или
повторная перезапись прекращает сессию. Awake и движение — отдельные факты в логах.

До первой записи append-журнал сохраняет session/entity и исходные часы;
flush/close/readback обязательны. При stop/ошибке/heartbeat timeout восстанавливаются
только поля, всё ещё содержащие значения патча. Чужие изменения не перезаписываются.
Частичный отказ второго setter допускает восстановление первого. Reload читает
журнал и выполняет только восстановление при той же уникальной identity/session,
никогда не возобновляет израсходованный Follow. Повреждённый журнал блокирует работу.
Новая сессия мира не получает старые часы по совпавшему entityId.

По исходнику lua_host/host.cpp file watcher отслеживает .lua и mod.json: допись
lease-журнала .jsonl сама по себе не вызывает reload. Float setter принимает
конечные float и не ограничивает их диапазоном часов.

Follow сохраняет алгоритм, 20/50 м X/Z, 2 м в 3D, маршрутизацию, лимиты и команды.
Runner опрашивает примерно раз в секунду; lease обслуживается каждый server tick.
Навигация, анимационные ресурсы, home/faction/inventory и saved-компоненты не
записываются. В installed каталог в этой задаче не записывалось ничего.

## Пакет и следующая проверка

Пакет `dist/stage10_15_movement_0_3_1`, exact manifest
`compatibility/experiments/stage10_15/exact-update-manifest.json`.
Пять замен: main.lua, follow.lua, follow_config.lua, mod.json, README.md.
Три добавления: schedule.lua, follow-stage10-15.lock, пустой schedule-stage10-15.jsonl.
Перед будущей установкой — свежий closed preflight и backup LOCAL23 + 5 замен = 28.
Старые Stage10.13/14 SPENT, spawn intent и журналы не заменяются.
Baseline — post-close-reviewed PID490800, SHA
`4e4e693d45581c004faa9f494252ec0c08d0ceced8cfe9004b1702f3b85edd45`.

После отдельного разрешения: установить exact8, проверить effective35, receipt,
backup и restore/removal dry-run. Пользователь вручную загружает LOCAL Body Test /
AI Body Test slot1/1. Новый Stage10.15 Runner проверяет exact EXE и версию 0.3.1;
одна отдельно разрешённая сессия180с, без ручного MOVE.

Подготовлены `scripts/install_follow_stage15.py` и `scripts/follow_stage15.py`.
Они не запускались в режиме установки/игровой сессии. Manifest SHA-256:
`ecfe74668d1aaa38ce8d40e7c41283b62d0253dbda66d3b0fa44ee3f40c550d2`.

Ночью: FOUND_ONE → SCHEDULE_ACQUIRED → NATIVE_WAKE_PENDING →
SCHEDULE_SLEEP_EXIT_REAPPLIED (если exit перевыбрал часы) → SCHEDULE_AWAKE_OBSERVED.
Затем реальные координаты/анимации и сближение при villager_move. Днём и при
переходе суток NPC не должен снова входить в sleep. В конце SCHEDULE_RESTORED;
после закрытия краткий аудит. Автоматического rollback нет.

## Границы и оставшиеся риски

- Реализован экспериментальный механизм. Native wake latency, анимация вставания
  и реальное ночное движение пока не проверены в игре.
- Перед отключением мода нужны f_stop и подтверждённое восстановление. Нет
  подтверждённого unload callback: принудительное выключение Lua/процесса может
  не дать выполнить cleanup. Журнал сохраняется; identity mismatch блокирует
  автоматическое восстановление в другую сущность.
- Identity — PROFILE_ONLY. Уникальность профиля не доказательство идентичности
  экземпляра. После перезапуска entityId не используется как постоянный ID.
- Сон и поход к кровати из-за ночи блокируются окном. **Независимые home/leash,
  сидение/разговор и native roaming не отключены**. Follow повторяет собственные
  штатные приказы в существующих пределах. Не заявляем полного подавления любого
  AI или работоспособности движения вне leash.
- При отличающемся exit/reroll будет SCHEDULE_CONFLICT/WAKE_TIMEOUT с остановкой,
  без случайной записи state. Неуспешный тест не разрешает автоматическую новую сессию.
- Прямой записи saves нет; штатные autosave после будущего теста могут сохранить
  последствия обычного AI. Проверка сохранений выполняется после игры.

Результаты офлайн-тестов: `compatibility/experiments/stage10_15/offline-validation.json`
и новая запись `docs/PROGRESS.md`. spawn_ready=false.
