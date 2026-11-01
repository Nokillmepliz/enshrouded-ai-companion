# Stage 10.9 — независимые safety gates и recovery

Реализация офлайн-контракта: `companion/safe_spawn.py`. Разрешённые статусы: `CONFIRMED`, `FAILED`, `UNKNOWN`, `NOT_APPLICABLE`. Последний допустим только с `risk_absence_proven=true`. У каждого gate обязательны reason, provenance, evidence, confidence и, где применимо, session/time.

## Текущее состояние

| Gate | Статус | Причина |
|---|---|---|
| INSTANCE_IDENTITY | UNKNOWN | native generation/atomic marker не найден |
| OWNERSHIP | UNKNOWN | ownership metadata не раскрыта |
| POSITION | UNKNOWN | нет read-only ground+clearance+walkability query |
| PERSISTENCE | UNKNOWN | lifecycle custom villager не проверен |
| FACTION | UNKNOWN | PlayerAlly подтверждён в template, dynamic AI не проверен |
| DESTROY | UNKNOWN | нет atomic identity check + destroy и postcondition runtime |
| TEMPLATE | CONFIRMED | Stage 10.7 load-only evidence v4 |
| WORLD_CONTEXT | UNKNOWN | Phase A runtime не выполнялся |

Любой обязательный `UNKNOWN/FAILED`, отсутствующий или некорректный gate блокирует spawn. Общий `safe=true` не формируется. `spawn_ready=false` задан независимо от результатов mocks.

## Recovery procedures

Все действия Phase A ниже read-only. Любая запись, destroy, rollback или restore требует отдельного прямого разрешения пользователя и нового preflight.

| Сценарий | Обнаружение | Без мутации | Stop condition | Возможное восстановление после разрешения | Нельзя гарантировать |
|---|---|---|---|---|---|
| NPC не появился | spawn result/evidence, exact scan | сохранить логи/hashes | outcome unknown | отдельный session review; без retry | что entity не появилась поздно |
| NPC невидим | identity + render levels | observer, screenshot пользователя | identity/render unknown | controlled destroy только при CONFIRMED | что это лишь render fault |
| NPC в геометрии | position/render observation | зафиксировать coordinates | не teleport/retry | targeted destroy либо full LOCAL restore | безопасное извлечение teleport |
| NPC враждебен | faction/AI/event evidence | пользователь выходит/закрывает игру | немедленно прекратить команды | full LOCAL restore предпочтительно | безопасный live faction write |
| NPC не удаляется | post-destroy presence ≥ timeout | продолжать read-only observation | не повторять destroy | отдельный atomic re-identification или restore | результат первого destroy |
| NPC после reload | unique identity/persistence scan | evidence + save hashes | identity не CONFIRMED | restore полного test LOCAL set | targeted destroy по старому ID |
| Дубликат | candidates > 1 | перечислить fingerprints без удаления | AMBIGUOUS | full LOCAL restore | какой экземпляр наш |
| EntityId reused | generation/marker mismatch | state `REUSED`, retain evidence | запрет destroy | только restore/новая сессия | foreign entity safety при ID destroy |
| Crash игры | process/log/evidence tail | hash audit после закрытия | outcome unknown | verified backup restore | завершился ли spawn/destroy |
| Bridge потерян | heartbeat/session mismatch | сохранить runtime files после закрытия | запрет retry/reconnect spawn | новый read-only preflight | состояние команды в полёте |
| Save изменился | baseline hash/size diff | классифицировать expected/unknown | unknown change | полный набор LOCAL, не отдельный файл | согласованность частичного restore |
| KFC/DAT изменены неизвестно | hash manifest | закрыть игру, собрать diff | integrity failure | штатный rollback по receipt | безопасность неизвестного файла |
| Backup устарел | manifest predates current baseline | ничего не восстанавливать | backup gate FAILED | новый verified backup до теста | восстановление актуального мира старым backup |
| Неизвестный persistent NPC | scan после reload/save diff | не искать жертву широким фильтром | ownership UNKNOWN | full verified LOCAL restore | targeted cleanup |

Evidence, которую сохраняют: session/run token hash, полный gate report, EntityId и все identity observations, component/template fingerprints, координаты, command accepted/sent/state/postcondition отдельно, Bridge/EMF/EML logs, install/KFC/DAT/LOCAL hash manifests. Приватный token и saves не публикуются.

Restore разрешён только когда игра/server закрыты, backup актуален и 100% проверен, целевой набор — исключительно LOCAL test character/world, пользователь отдельно разрешил действие, а post-restore integrity plan готов. Частичный KSD edit запрещён.
