# Архитектура и проверяемый roadmap

Lua Body Adapter + Python Bridge сохраняются. Замена game adapter не должна требовать переписывания личности/памяти/LLM.

| Слой | Ответственность / граница |
|---|---|
| AI Core (Python) | Personality, LLM, memory, conversation/context, планирование; стабильный companion UUID, не entityId |
| Companion Controller | Orders/tasks, follow/combat/inventory policies, cancel/recovery; каждый запрос с session/identity/result evidence |
| Game Adapter | EMF/Lua/Bridge, EML template, lifecycle/navigation/components; только подтверждённые API |
| Compatibility | Build/API/source/DLL hashes, profiles, receipt/baseline, safety gates, evidence; fail closed |

Сейчас реализована часть adapter/contracts, полноценного Brain/voice нет. Upstream Companion можно изучать/переиспользовать по MIT с notices; его Vukah lifecycle нельзя сделать общей основой без сохранения наших safety gates. Beastmaster roster полезен как пример отделения личности от body; Villager Jobs — tasks/cancel/local movement.

| Этап | Зависимости и конкретный результат | Done / блокеры / reuse |
|---|---|---|
| Clean recovery | B backup/quarantine → manual Steam Verify → audit | KFC/DAT/source clean evidence; unknown files/depot hashes сейчас блокируют |
| Migration | Clean base + единственный owner | Patch0.5, finalized observer/capture, pinned plan; reuse integrated EML |
| Load acceptance | Разрешённые E/F, ручной запуск | Source/clone typed fields, shadow readback/writer/session; render UNKNOWN, spawn=false |
| Первый humanoid render | Отдельный spawn review, identity/position/lifecycle gates | Один контролируемый экземпляр, визуальное подтверждение пользователем, cleanup proof; сейчас заблокирован |
| Instance lifecycle | Identity primitive + persistence policy | No duplicate/reuse, dismiss observed absent, crash/reload recovery; minimal native gap |
| Movement | Body/lifecycle accepted | Reachable point, ARRIVED/STUCK/TIMEOUT/cancel; reuse ground/path/villager_move |
| Follow | Movement + подходящий native AI/leash | Длительный маршрут, препятствия, дистанция/ночь/reload; близость NPC не PASS |
| Inventory | Verified transactions + body support | Move item и ledger consistency, failure/reload; reuse EMF transfer semantics |
| Equipment | Inventory + visual component proof | Реально видимое надевание/снятие и анимация; Companion level bonus не DONE |
| Combat | Faction/target/health/ownership | Controlled target selection, отсутствие friendly fire, death recovery; reuse Beastmaster policies |
| Voice | Read-only audio I/O interface | STT/TTS с ошибками/cancel; не зависит от game entityId |
| LLM | Validated bounded commands | Model не вызывает mutations напрямую; controller проверяет каждый запрос |
| Memory/personality | Stable logical UUID | Sessions/reload не теряют личность; body replacement не новая личность |
| Autonomy | Все выше + budgets/interrupt | Последовательность задач с результатами/recovery; контролируемые игровые проверки |

Roadmap сокращён за счёт reuse navigation/ground/controller patterns вместо нового общего movement engine. Не добавляется пустой «этап исследования всего»: у каждой границы конкретный artifact и критерий. Голос/Brain не включаются в текущую разработку.
