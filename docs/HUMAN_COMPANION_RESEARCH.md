# Исследование человекоподобного тела AI Companion

Дата: 30.10.2026. Исходники закреплены: EMF 0.3.2 — `08d600155fcadc8e45cc9c6f3932a67c717345be`, Enshwick — `135561192969af9ec9ffd0957b97ca6a7aa31820`. Игра не запускалась, сущности и сохранения не изменялись.

Статусы: **CONFIRMED** — подтверждено исходником или зафиксированным runtime-исследованием; **LIKELY** — обоснованная гипотеза; **UNKNOWN** — данных недостаточно; **UNSUPPORTED** — подтверждённого безопасного пути в текущем API нет.

## Вывод

Наиболее перспективен **вариант C**: штатный workshop survivor как человеческое визуальное/физическое тело плюс отдельные контроллеры Companion. Однако runtime-прототип заблокирован. Игра поддерживает один экземпляр каждого survivor и удаляет дубликаты; прямой `emf.spawn` этих шаблонов, начальная faction, ownership, безопасный dismiss и бой независимого экземпляра не проверены. [Enshwick описывает один entity на survivor и uniqueness pass](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/book/src/survivors.md#L1-L24), а исследование EMF для build 1273043 фиксирует `ForceSave` и уничтожение дубликатов по template GUID ([источник](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villages.md#L129-L137)).

До read-only survey и отдельного игрового протокола ни один человеческий шаблон не включён в runtime allow-list. `Enemy_Vukah_Melee` остаётся только историческим legacy-профилем и не является направлением разработки.

## Реальные кандидаты

Enshwick содержит 18 workshop survivors с `npcId`, staff GUID и template GUID; `npcId` равен FNV-1a template GUID. Это реальные идентификаторы из игровых данных, а не придуманные имена ([таблица upstream](https://github.com/enshwick/enshwick/blob/135561192969af9ec9ffd0957b97ca6a7aa31820/crates/enshwick/src/survivors/workshop.rs#L150-L190)).

Закреплённый Enshwick — отдельный upstream и не является бинарным доказательством состава установленного build 1273043; его собственная документация имён упоминает build 1269579. Поэтому все GUID считаются подтверждёнными кандидатами из game data, но их наличие и components на build 1273043 должны быть повторно подтверждены read-only survey.

Общие свойства всех строк:

- источник и template: **CONFIRMED**;
- человеческий townsfolk-облик: **LIKELY** до model survey/скриншота конкретного шаблона;
- direct `emf.spawn`, начальная faction и безопасный dismiss независимого дубля: **UNKNOWN**;
- типовая идентичность `template + ActiveNpcState.npcId`: **CONFIRMED**, уникальная идентичность экземпляра: **UNKNOWN**;
- `NpcCommandEvent.GoToPosition` для уже существующего active NPC: **CONFIRMED** на build 1273043 ([runtime-запись EMF](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villager_jobs.md#L16-L18)); постоянный follow: **UNKNOWN**;
- combat, оружие и броня: **UNKNOWN**;
- `InventorySetup` у villager: **LIKELY/частично CONFIRMED** для игрового NPC; пригодность как собственного инвентаря компаньона: **UNKNOWN**.

| Кандидат | Template GUID | npcId | Оценка |
|---|---|---:|---|
| blacksmith | `c313f0a8-ed2e-444e-8384-a540f6bbd98e` | 1201801546 | Основной взрослый NPC; риск конфликта с игровым кузнецом |
| blacksmith_assistant | `04d42ed2-beb4-4013-8f10-5d63efae2015` | 1731045065 | Приоритет для survey; отдельный штатный survivor, но всё ещё unique |
| alchemist | `7456862b-53fe-4b94-8a75-d3079afc9323` | 4057418535 | Фиксированный workshop survivor |
| alchemist_assistant | `27e2fb44-4975-4b61-988d-c7b4e16ed325` | 3159593666 | Приоритет для survey |
| carpenter | `8045836c-0647-4a0a-9a00-7d299b4599f8` | 2103948589 | Фиксированный workshop survivor |
| carpenter_assistant | `31ff0824-2c28-4934-a236-d3aa5c0306b9` | 2031808579 | Приоритет для survey |
| hunter | `a6db3870-a426-494e-a203-64789389e7d7` | 2242206866 | Тематически подходит для оружия, но combat не подтверждён |
| hunter_assistant | `e3736dff-0ad2-47fc-903c-66c1775836e8` | 1633192162 | Лучший первый survey-кандидат; боевые возможности всё равно UNKNOWN |
| farmer | `1b533365-f465-42e0-a51f-7d66e9cf3659` | 974506154 | Фиксированный workshop survivor |
| farmer_assistant | `a6bab01b-a848-4645-84fb-6ae22b532eb0` | 1669027340 | Приоритет для survey |
| bard | `23a61977-ae52-443d-ab6f-23826a2cda5a` | 218342694 | Человеческие анимации LIKELY, combat UNKNOWN |
| bard_assistant | `ff6cd2cf-b566-482c-ba14-075d1a918b3d` | 1640210983 | Приоритет для survey |
| crypt_keeper | `b61da3e5-b8f2-4933-84f8-48e7ecfcba39` | 757847452 | Фиксированный workshop survivor |
| crypt_keeper_assistant | `aa51d579-d35f-433e-be91-d4f7133d62c5` | 2159156280 | Приоритет для survey |
| barber | `f63dc05f-88ed-4f5a-9640-1d19d980bb37` | 3689431984 | Человеческий внешний вид LIKELY |
| researcher | `35afe333-75a0-45ec-90d4-5abddb08fdc5` | 1095951179 | Человеческий внешний вид LIKELY |
| trader | `877ab652-90f8-45da-8865-70e4e0fedc57` | 2797365275 | Имеет NPC workshop/trade-систему; это не companion inventory |
| fisher | `e7666cd3-e530-4f9d-9586-519e4ab969dc` | 4192796482 | Фиксированный workshop survivor |

Выбор для **следующего read-only исследования**: `hunter_assistant`, затем `blacksmith_assistant`. Выбор для spawn пока: **ни один**.

## Сравнение вариантов

| Вариант | Что подтверждено | Блокеры | Решение |
|---|---|---|---|
| A. Существующий человеческий NPC | Реальные templates/npcId; штатные модель, анимации, roaming и `GoToPosition` | Unique survivor, `ForceSave`, конфликт с квестовым NPC, direct spawn/faction/ownership/dismiss UNKNOWN | Использовать как источник данных и первый survey, не как готовое тело |
| B. NPC на основе player | В движке есть `PlayerInput`, `Equipment`, `VisualEquipment`, `Inventory` структуры | Нет подтверждённого API создания независимого player entity без клиента/account authority; наличие компонентов не доказывает рабочий player clone | **UNSUPPORTED** текущими доказательствами |
| C. Гуманоид + собственные системы | Можно отделить Brain от body; survivor даёт человеческую модель/анимации и движение | Сначала нужен безопасный lifecycle; настоящий inventory/equipment/attack ещё не подтверждены | **Рекомендуемая долгосрочная архитектура**, runtime spawn пока BLOCKED |

## EMF API и идентификация

EMF умеет spawn по template GUID, читать/писать компоненты и читать template-half компонента. Lua `world:template(component,id)` возвращает конкретный template component, например `ModelResource.model`, но не template GUID сущности ([Lua API](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L160-L183)). `EntityId` остаётся `uint32`; generation ID экземпляра публично не предоставлен.

Для survivor доступен сильнее типовой fingerprint:

`session + entityId + ModelResource.model + ActiveNpcState.npcId + kind=active_npc`.

Он должен появиться полностью несколько последовательных callback, а любое расхождение необратимо снимает доверие. Это лучше одного EntityId, но не различает мгновенную замену полностью идентичным экземпляром между наблюдениями. До read-only model survey неизвестен ожидаемый `ModelResource.model`, поэтому gate остаётся BLOCKED.

Spawn безопасен только если до активации доказаны: доступность полного fingerprint, исходно невраждебное/неактивное состояние, отсутствие конфликта uniqueness, ownership и проверяемый dismiss. Подтверждённого API «spawn inactive, затем activate» не найдено. Переставлять faction write до идентификации небезопасно: это запись в неподтверждённый ID.

## Инвентарь

**Что есть:**

- Сгенерированы `Inventory`, `InventorySetup`, `Equipment`, `RenderEquipment`, `VisualEquipment` и связанные события. Это подтверждает структуры, но не наличие всего набора на каждом NPC.
- Lua 1.9 предоставляет `emf.put`, `emf.take` и `emf.give`; `take` all-or-nothing и возвращает предметы, если callback не передал их дальше ([API](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/modding/lua.md#L100-L108)).
- EMF runtime-исследование подтверждает inventory transactions и `InventorySetup` у villager, а также использование chest как оператора crafting ([источник](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_villager_jobs.md#L3-L18)).
- Стабильный ItemId — FNV-1a-32 GUID предмета; gear с уникальными свойствами имеет отдельный pide entity. Простого `(itemId,count)` для брони/оружия недостаточно.

**Чего нет:**

- Не подтверждено, что inventory survivor подходит как долговременный личный backpack компаньона и сохраняется без побочных эффектов.
- Последовательность `take → callback → put` через Lua не доказана атомарной между двумя владельцами при reload/crash.
- Собственный sidecar JSON может хранить логический ledger, но не является настоящим игровым inventory. Без подтверждённого escrow-контейнера он создаёт риск дублирования или потери.
- Безопасная передача gear должна сохранять pide, Level, perks, durability и gem. Исследование прямо оставляет выбор holding container и save/load поведения открытым ([детали](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/docs/engine_parts/re_take_items.md#L189-L224)).

Вердикт: настоящий Companion Inventory — **UNKNOWN/BLOCKED**. Реализация выдачи, передачи и сохранения предметов на этапе 6 запрещена.

## Экипировка, навигация, бой и взаимодействия

- **Equipment:** структуры и player transaction path существуют, но публичного Lua `equip(entity,slot)` нет. Внутренний `equipItem` зависит от current iterated entity и не проверен для survivor. **UNKNOWN**.
- **Movement:** `NpcCommandEvent.GoToPosition` существующего active survivor — **CONFIRMED**; команда затухает, и villager возвращается к roaming. Постоянный follow потребует повторной отправки и runtime-проверки, это не доказанный follow.
- **Combat:** API приказа survivor атаковать цель не найден. Наличие hunter-модели/оружия не доказывает боевой AI. **UNKNOWN**.
- **Interaction:** отдельные события crafting/loot подтверждены для конкретных сценариев. Универсального `interact(npc,object)` нет. **UNKNOWN**.
- **Animations:** штатный survivor имеет собственный animation graph **LIKELY**, но произвольный play-animation API не подтверждён.

## Реализованный офлайн-результат

- `companion.human_body` содержит закреплённый каталог 18 кандидатов, evidence-aware capabilities и запрещает runtime-выбор всех кандидатов.
- `IdentityGate` требует ожидаемый model GUID и три последовательных полных наблюдения; неполный fingerprint, reflection error, timeout, смена session/entity/model/npc/kind блокируют доверие и удаление.
- Старые GUID Vukah/маркера вынесены в `body_profiles.lua` как `legacy_vukah`; generic lifecycle больше не содержит эту зависимость напрямую.
- Команды `spawn/follow/stay/moveTo/attack/interact/dismiss` для Human Body **не объявлены реализованными**.

## Следующая безопасная проверка

1. Подготовить отдельный read-only survey-мод на основе уже существующих upstream `guid_dump`, `model_survey` и `npc_explorer`.
2. В отдельной подтверждённой LOCAL-сессии без spawn экспортировать template components для `hunter_assistant` и `blacksmith_assistant`: `ModelResource`, `Faction`, `ActiveNpcState`, `ActiveNpcStateSaved`, `Inventory`, `InventorySetup`, `Equipment`, `VisualEquipment`, save/network markers.
3. Проверить, присутствуют ли кандидаты уже в мире, и не трогать их.
4. По результату выбрать один template и спроектировать protocol revision 3. Если нельзя доказать изначально безопасный lifecycle, spawn останется заблокированным.

## Ответы на пять вопросов

1. **Можем ли создать NPC, похожего на обычного игрока?** Реальные человеческие survivor templates есть, но безопасное создание независимого экземпляра пока **UNKNOWN/BLOCKED**.
2. **Может ли он иметь настоящий inventory?** Компоненты и транзакции есть, но пригодность и сохранность inventory независимого companion не подтверждены: **UNKNOWN**.
3. **Оружие, броня, инструменты?** Движок поддерживает equipment игрока, но equip path survivor не подтверждён: **UNKNOWN**.
4. **Движение и бой через EMF?** `GoToPosition` существующего survivor — **CONFIRMED**; follow и combat-control — **UNKNOWN**.
5. **Конкретный следующий шаг?** Read-only component/model survey двух assistant templates, затем выбор тела и проектирование безопасного protocol v3 без spawn до отдельного разрешения.
