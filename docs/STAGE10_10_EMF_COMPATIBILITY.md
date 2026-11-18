# Stage 10.10 — EMF

На 2026-11-18 последний release и stable — **v0.6.18**, опубликован 17 ноября в
22:47:55 UTC. [Release](https://github.com/matenm/emf-enshrouded/releases/tag/v0.6.18),
[API releases](https://api.github.com/repos/matenm/emf-enshrouded/releases),
[commit fa6efdac2d93dd1d8ac6fe0e2a658140aec35241](https://github.com/matenm/emf-enshrouded/commit/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241).
Исследованный checkout master совпал с тегом. Экспериментальная сборка не выбиралась.

| EMF | Game build | Native API / Lua host | Source support | Бинарник / наш runtime |
|---|---:|---|---|---|
| 0.3.2 / 08d6001 | 1273043 | 20 / исторический host | SUPPORTED исторически | Stage 10.7 LOAD_ONLY_SUCCESS |
| 0.3.2 / 08d6001 | 1287369 | 20 | UNSUPPORTED | старый локальный лог: missing required signatures |
| 0.6.18 / fa6efda | 1287369 | 46 / 1.39.0 | SUPPORTED по upstream | release hashes проверены; наш runtime UNKNOWN |

`hello.api` — номер core/native API, доступного Lua host; версия самого Lua-мода
отдельна. Записи «Lua API 20» в старых отчётах не означают Lua language version.
Типы/offsets и исправления после обновлений разобраны в
[ENGINE_MAP](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/docs/ENGINE_MAP.md#L76-L138).
Полный ABI: [emf_api.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/sdk/include/emf/emf_api.h).

Официальный `EMF-0.6.18-manual.zip` скачан только в `runtime/stage10_10/`:
11 516 333 bytes, SHA-256
`12bbcae2e52386bcd7f1747701bb6d1ec8a64fab061e6e33ce994b6ee29c926b`.
Совпал с digest GitHub release API. 306 файлов, полный
[список и хеши](../compatibility/audits/1287369/release-files.json).

| DLL | SHA-256 |
|---|---|
| game/dinput8.dll | `8556928e903095714ed5b355f6e951bd9311a1a3405b9338604e6a56daa3d9e5` |
| game/emf/emf_core.dll | `b1cd6c31f19598fb0d404e0556b744f03cf0e1c25d78c6ac64f9125f2cb3e763` |
| game/emf/emf_content.dll | `c5924068a5cfc27ce6508d153c75b7a1a90964ecb87996ebb5fc8356584cb691` |
| game/emf/mods/lua/lua.dll | `621c6bd10acfaf584f9e2a055fb0e1606c22754753de367788ec1c27ac98c8e4` |

Четыре DLL извлечены в ignored project folder для статического PE-аудита:
x64/PE32+, Authenticode **NotSigned** у всех. Import table содержит Windows DLL
(KERNEL32, USER32, ADVAPI32, IMM32, ole32, SHELL32, ntdll, bcryptprimitives,
api-ms-win-core-synch); это не исключает dynamic loading и не доказывает безопасность.
Архив включает install/uninstall CMD/PowerShell, `tools/emf_sigcheck.exe` и много
необязательных модов. Они не исполнялись, автоматическое копирование всего архива недопустимо.

[Issue 45 о подписи](https://github.com/matenm/emf-enshrouded/issues/45) описывает
quarantine Nexus и отсутствие code signing. Это объяснение автора, а не независимый
антивирусный verdict; детальные Nexus-детекты и воспроизводимая идентичность DLL
исходникам не установлены. Совпадение release digest подтверждает скачанный asset,
но не reproducible build. Антивирус и защита Windows не отключались.

Новые ground/path/villager APIs и оставшиеся ограничения:
[Stage 10.9 revalidation](STAGE10_10_STAGE10_9_REVALIDATION.md).
Установку всё ещё блокируют состояние игры, выбор content loader и evidence export.
