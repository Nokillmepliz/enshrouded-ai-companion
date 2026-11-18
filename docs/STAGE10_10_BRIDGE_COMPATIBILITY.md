# Stage 10.10 — Python Bridge и observer

Протокол EMF остаётся **1**: локальный named pipe `emf-bridge-<pid>`, UTF-8 JSONL,
request `{id,cmd,...}`, correlated reply `{id,ok,...}`, events без id.
В `hello` отдельно доступны `emf`, `api`, `game_build`, `process`, `pid`, `protocol`.
[Wire contract](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/modding/debug_bridge.md#L121-L174).

Limits: request 64 KiB, reply 1 MiB, console output 512 KiB с `truncated`; 8
ожидающих requests и 8 console lines. Console timeout 1–120000 ms, default 10000;
settle 0–5000 ms. Reply `ran` означает выполнение команды, не game-state proof.
Ошибки `timeout/busy/unavailable/bad_request/unknown_command/refused` различаются.
Replies могут приходить не по порядку; совпадение id обязательно.

[Новый Python client](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/tools/bridge/emf_bridge.py#L345-L448)
проверяет PID владельца pipe, имеет deadline и закрывает соединение при timeout.
Для console default deadline включает 10 s command + settle + 15 s margin.
Смена session/world и поздний ответ не должны разрешать повторное действие.
Upstream run token отсутствует в wire handshake: **наш** per-install run token
принадлежит observer/evidence. Его нельзя выдавать за protocol authentication.

Остались `emf.command`/`emf.reply`, host/server callbacks и JSON output, необходимые
observer. Новый Lua host — 1.39.0, core API46. Сам wire migration не требуется;
build/API/version gates нашего клиента необходимо менять через профиль,
сохраняя строгую проверку LOCAL-контекста и session. Старый `BodyClient` по-прежнему
отказывается от нового build — mutation path для 1287369 не открыт.

Реализован **offline** `validate_observer_capture` в
[compatibility.py](../companion/compatibility.py). Он принимает проектный capture
envelope, а не выдуманный расширенный EMF reply. Будущий collector должен связать
hello/world/session с ответом observer и новым install token. Проверяются только
`status`, `inspect`, `compare`; `spawn`, `dismiss`, raw `console`, `load_world`
отклоняются этим контрактом. Проверены mismatch protocol/build/session/response
version/token, read_only/spawn_forbidden, включая ошибочный boolean как integer.

Реального pipe connection в Phase A не было. Reader/observer в игре не обновлён.
Нельзя назвать `status/inspect/compare` runtime-tested на 0.6.18.
Дополнительный blocker: observer 0.4.0 читает `export/.../template_evidence_v4.txt`,
а integrated content не делает EML export. До выбора канала evidence новый
runtime collector/observer не выпускается. В будущей Phase C сначала hello/state,
затем три разрешённые namespaced команды, с correlation и свежими log offsets;
никаких console-команд управления миром или NPC.
