# Stage 10.9 — faction, AI и destroy

Дата: 2026-11-01. Runtime не выполнялся.

## Faction и агрессия

EML patch 0.4.0 устанавливает template `Faction=PlayerAlly (11)` до создания entity. Тип `Faction` — один байт, `PlayerAlly=11`: [components.hpp L10811–10837](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/sdk/include/emf/generated/components.hpp#L10811-L10837). Это подтверждает data-only начальное значение, но не dynamic faction после spawn и не отсутствие другого AI, которое выберет/атакует цель.

Исходный villager template использует `ActiveNpcState` и villager programs. Карта программ показывает отдельные enemy states (`Enemy01BehaviorState`, `DynamicEnemy01BehaviorState`) и faction-dependent systems, но отсутствие одного enemy component не является полной гарантией пассивности. `update_pacified_state` читает faction и HitEvent, что также показывает различие faction и поведения: [ecs_programs.md L778–788](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/ecs_programs.md#L778-L788).

Для первого visual template требуются: template faction 11; dynamic faction 11 сразу после spawn и несколько ticks; отсутствие enemy behavior/attack target; отсутствие hostile events/animation. Удаление combat-компонентов без полного dependency graph не выполняется. Предпочтительный вариант остаётся passive villager без follow, inventory и combat commands. Gate `FACTION=UNKNOWN` до runtime.

## Destroy

`emf.destroy(world,id)` разрешён только в callback server world. Core запрещает player по наличию `PlayerState`, затем вызывает native `DestroyEntity`; `true` означает отсутствие SEH, а не наблюдённое исчезновение: [api.cpp L757–771](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/api.cpp#L757-L771), [spawn.cpp L24–30](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/core/spawn.cpp#L24-L30).

Будущий `destroy_owned_entity(identity)` должен:

1. в одной world-thread native операции сверить session, instance marker, generation/equivalent, template identity и EntityId;
2. отказаться при `AMBIGUOUS/STALE/REUSED/LOST`, нескольких candidates или player component;
3. вызвать destroy без возврата управления между check и call;
4. считать вызов только `ACCEPTED_UNVERIFIED`;
5. подтвердить отсутствие минимум в трёх последовательных server ticks;
6. отдельно проверить отсутствие повторного появления после lifecycle/reload.

Проверка Lua/Python, затем отдельный `emf.destroy`, имеет TOCTOU: ID может быть повторно использован между операциями. Повторный destroy после timeout/crash запрещён, пока identity не доказана заново. `destroy=true`, краткое исчезновение и отсутствие ID в одном tick недостаточны.

Офлайн функции `authorize_destroy()` и `verify_destroy_result()` реализуют этот контракт, но не вызывают EMF. Текущий gate `DESTROY=UNKNOWN`; существующего Lua API недостаточно.
