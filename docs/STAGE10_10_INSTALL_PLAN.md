# Stage 10.10 — Phase B plan, BLOCKED

**Не выполнять сейчас. `installation_ready=false`.** Это план review, не готовый
transaction manifest. Нет согласованного content owner, verified clean baseline
1287369 и готовой пары patch0.5.0/observer. Неизвестные хеши не заполняются фиктивно.

Game root: `D:\SteamLibrary\steamapps\common\Enshrouded`.
LOCAL root: `C:\Users\user\Saved Games\keen games\Enshrouded`.
Пакет: `C:\Enshrouded-ai-companion\runtime\stage10_10\EMF-0.6.18-manual.zip`.

Последовательность **только после отдельного разрешения и закрытия блокеров**:

1. Проверить отсутствие `enshrouded.exe` и `enshrouded_server.exe`, EXE/Steam identity.
2. Повторить inventory и сравнить каждый planned target с опубликованным before hash.
3. Создать verified backup текущего mixed state, изменяемых mod files и всех LOCAL
   saves. Полная 48-ГБ копия игры не нужна; исходные DAT хешируются, touched data
   сохраняются по конкретному плану. Старые копии не удаляются.
4. Review exact cleanup manifest: текущие пути/hashes/ownership и restoration source.
   Не использовать старый cross-build rollback. DAT055–063 не удалять по номеру.
5. Отдельно согласовать получение clean baseline (возможен Steam Verify пользователем).
   После него проверить отсутствие чужих loaders/artifacts, не считая Verify их удалением.
6. Заново извлечь source/resources, проверить GUID/npcId collision, типы, visual closure,
   все DAT; сохранить verified clean backup с EXE/build/manifest identity.
7. Выбрать **одного** content owner; выпустить reviewed patch/observer и evidence channel.
8. Создать exact install plan с каждым destination/before/after SHA, новый run token
   и новый receipt. Старые receipt/token не переиспользовать.
9. Установить только согласованный allowlist; все прочие mods выключить, учесть
   loader auto-discovery. При антивирусной блокировке остановиться без обхода.
10. Проверить installed SHA, версии/профиль/пути evidence, config, mutation prohibition,
    new-build rollback dry-run. Остановиться до отдельного разрешения Phase C.

Кандидаты нового EMF из официального архива; все paths ниже относительны game root.
Полный after hash для каждого archive file — в
[release-files.json](../compatibility/audits/1287369/release-files.json), ключ
`EMF-0.6.18-manual/game/<path>`. Before hashes — в
[file-inventory.json](../compatibility/audits/1287369/file-inventory.json).

| Назначение | Пути | План восстановления при будущем разрешении |
|---|---|---|
| EMF loader/core | `dinput8.dll`, `emf/emf_core.dll` | exact before copy из нового backup; старый DLL не считать рабочей конфигурацией новой игры |
| Console layer | `emf/vk/VkLayer_EMF_console.json` | восстановить before либо удалить, если receipt подтверждает создание |
| Lua host | `emf/mods/lua/lua.dll`, `emf/mods/lua/mod.json` | current-build receipt с точными before/after |
| Console fonts | `emf/fonts/Alegreya-Bold.ttf`, `Alegreya-Regular.ttf`, `CascadiaMono-Regular.ttf` | receipt-bound before/after |
| Tool identification | `emf/known_tools.txt` | receipt-bound before/after |
| Content owner option 1 | standalone `dbghelp.dll`, `eml.json`; integrated content off/absent | новый backup actual-build KFC/resources + точная атрибуция outputs |
| Content owner option 2 | `emf/emf_content.dll`; standalone dbghelp absent | exact shadow manifest; original data integrity; path/hardlink review |
| Core/Bridge config | `emf/emf_core.ini` | сохранить before; after **не определён до review** |
| Patch/observer | `mods/aic_eml_humanoid/...`, `emf/mods/aic_template_observer/...`, observer config | новые paths/after hashes **не определены**, блокируют установку |

Основные DLL after SHA перечислены в [EMF audit](STAGE10_10_EMF_COMPATIBILITY.md).
Нельзя копировать целиком архив, запускать `install.cmd/.ps1`, устанавливать
Companion/Beastmaster/Villager Jobs/прочие gameplay mods, frametime overlay или
`emf_sigcheck.exe` только потому, что они находятся в официальном пакете.
Tools/docs/setup scripts не нужны в минимальном install allowlist.

Не объявлять rollback готовым для нового build на основании исторического 9/9.
Если known before target изменился между review и apply — остановиться;
unknown files и receipt вручную не исправлять. LOCAL saves при rollback не
восстанавливаются без отдельного разрешения.
