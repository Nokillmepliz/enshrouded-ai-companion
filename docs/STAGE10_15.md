# Stage10.15 — ночное расписание спутника

**Обновление:** это исторический отчёт первого прохода. Блокер ниже снят
статической проверкой EXE1287369 и реализацией Movement0.3.1; см.
[реализацию и ограничения](STAGE10_15_IMPLEMENTATION.md). Игровая проверка ещё не выполнена.

2026-11-22. **BLOCKED_NO_VERIFIED_PER_NPC_SCHEDULE_OVERRIDE**.
Причина ночного отказа установлена. Безопасное отключение расписания и корректное
пробуждение существующего NPC не реализованы: критерий «Follow в любое время»
не достигнут. Готового установочного патча или игровой сессии Stage10.15 нет.

## Что произошло в PID490800

В66 samples один NPC, ai_state8/decision5, неподвижен;64 WAITING_FOR_NPC,
0 Ground/Path,0 villager_move. Пользователь подтвердил ночь. SHA исходного журнала
2eb241e7b6cbf2c2c6f0379dd049d8be6c53e2968056acf1d8ed9d24de2d1717.

В [EMF villager_moves.cpp](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp#L51)
state8 явно назван Sleep, decision5 — WantsToSleep. paused() возвращает true
при любом из этих признаков; также блокируются Start,FindBed,InsideWater и
некоторые взаимодействия. Наш follow.lua ждёт при8/5 ещё до навигации.
Таким образом непосредственно наблюдалась блокировка в Lua; блокировка внутри
villager_move установлена по исходникам, а не по отправленному ночному приказу.
Удаление Lua guard не решает проблему: native executor продолжит ждать.

## Механизм штатного AI

Локальные исходники EMF0.6.18, commitfa6efdac2d93dd1d8ac6fe0e2a658140aec35241:

- [State machine](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/engine_parts/ai.md#L92):
  Start выбирает NpcCommon.sleepTime/wakeUpTime из шаблонного sleepSetup.
  DecideTask и CheckInterrupts проверяют ShouldSleep; при желании спать идут
  FindBed→GoToTarget/Sleep. Отсутствие кровати не отключает сон на земле.
- [Sleep и SetState](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/engine_parts/ai.md#L115):
  сон запускает последовательность анимации и actor flags. Нормальный выход
  выполняет exit/enter, сбрасывает path walker/таймеры, перевыбирает часы сна.
  Прямая запись state=Idle пропускает эти операции.
- [Распорядок/interrupts](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/engine_parts/ai.md#L191):
  кроме сна выбираются idle/inspect/sit/roam и общение. Удаление roamWeight не
  отключает ShouldSleep. Нулевой roamingRange означает stay и мешает движению.
- [Home/leash](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/core/villager_moves.cpp#L136):
  область дома остаётся независимым ограничением; home и saved-поля не меняем.

**Граница доказательств:** engine_parts/ai.md описывает статический анализ
сборки1269579. Установлена1287369. Его адреса SetState/ShouldSleep нельзя
использовать как подтверждённые адреса текущей игры. Поля и enum есть в SDK,
но безопасная семантика нового override из одного наличия поля не следует.

## Почему нет безопасного минимального патча сейчас

| Вариант | Что подтверждено | Чего не хватает |
|---|---|---|
| Удалить Lua sleep guard | Native move всё равно paused | Не даёт независимости от ночи |
| Записывать state/decision каждый tick | Компоненты доступны | Пропускает выход из сна, вмешивается в навигацию/анимации |
| Изменить sleepTime/wakeUpTime | Поля NpcCommon существуют | Точное условие интервала, equal/zero/wrap semantics в1287369; повторная генерация при выходе |
| Патч clone.sleepSetup | Можно изолировать от остальных шаблонов | Не доказан no-sleep набор значений и влияние на уже спящего существующего NPC |
| GoToPosition event | Штатное событие существует | Не отключает ShouldSleep на следующем tick; выход из сна требует текущей проверки |
| Reset event | Штатное событие существует | Меняет home/телепортирует, не подходит |
| Хук ShouldSleep/SetState | Есть старый статический разбор | Нет проверенных сигнатур/контекста1287369 и обратимого per-NPC API |

[Lua API](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/lua.md#L784)
не предоставляет отдельной подтверждённой операции wake/schedule override для
villager. world:template read-only; world:get позволяет писать данные, но это
не равнозначно штатному переходу состояний. Глобальный Daytime, actor flags,
sleepSequence, переходы всех NPC и таймеры по выдуманным значениям не менялись.

## Выполненный код и тесты

Добавлен чистый read-only анализатор companion/npc_schedule.py: раздельно
показывает Sleep и WantsToSleep, сохраняет границы session/entity при анализе
переходов. Не выводит время суток из AI state и не объявляет awake достаточным
для движения. Он не подключён к игровым командам и ничего не записывает в игру.
Результат анализа: compatibility/experiments/stage10_15/schedule-analysis.json.

55/55 целевых тестов PASS,0.170с (schedule analyzer + Follow). Проверены sleep
и sleep intent по отдельности, наблюдаемый переход roam→find-bed→sleep→awake,
смена сессии, неоднозначная идентичность и запрет ложной готовности. Старые
Follow-тесты подтверждают неизменность20/50м и маршрутизации. **Это не тесты
работающего пробуждения/приоритета ночью:** соответствующего механизма ещё нет.

## Следующий необходимый шаг

Для реализации нужна узкая проверка ShouldSleep, sleep exit и command handler
именно сборки1287369: условия интервала и штатный per-entity переход с exit/enter.
После подтверждения — либо clone-only template policy плюс безопасный wake,
либо адресный native API с lease на конкретную session/entity/npcId. Не глобальный
хук для всех NPC и не постоянная запись state. При неоднозначной идентичности
override запрещён. Снятие lease/ошибка/смена мира должны прекращать override.

Только затем возможны содержательные тесты day→night/night→day, уже спящий NPC,
сохранность чужих NPC, анимации/навигации и передача приоритета Follow. До этого
exact install manifest с runtime payload был бы ложной готовностью. Новое
разрешение на установку само по себе этот технический блокер не устраняет.

Ничего не установлено, игра не запускалась, NPC не создавался. Старые SPENT,
lock/intent/журналы сохранены; follow.lua, home, расписание и сохранения не менялись.
