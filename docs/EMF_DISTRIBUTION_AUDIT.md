# Аудит дистрибутива EMF 0.3.2

Дата проверки: **2026-10-30**

Вердикт: **`READY_FOR_BACKUP_AND_INSTALL_REVIEW`**

Этот вердикт означает, что конкретный официальный архив получен, его происхождение и состав проверены настолько, насколько это возможно без запуска бинарников, а установленная сборка игры присутствует в таблице совместимости EMF. Он не означает, что бинарники доказанно безопасны или что EMF уже испытан в игре. Перед установкой всё ещё нужны проверенная резервная копия и отдельное разрешение пользователя.

Во время аудита EMF не устанавливался, файлы в каталоге Enshrouded не копировались, игра и скачанные PE-файлы не запускались, сохранения не изменялись, защита Windows не отключалась.

## Проверенный файл

| Поле | Значение |
|---|---|
| Официальный источник | [GitHub Release EMF 0.3.2](https://github.com/matenm/emf-enshrouded/releases/tag/v0.3.2) |
| Архив | `EMF-0.3.2-manual.zip` |
| Локальный путь | `C:\Enshrouded-ai-companion\artifacts\emf-0.3.2-audit\EMF-0.3.2-manual.zip` |
| Размер | 5 142 221 байт |
| SHA-256 | `737d3614b9462f00e942828869054b842e7af6d7b9abe56402e2a0bde35d00d9` |
| GitHub asset digest | `sha256:737d3614b9462f00e942828869054b842e7af6d7b9abe56402e2a0bde35d00d9` |
| Состав | 239 записей, 12 982 114 байт после распаковки |
| Локальная проверка Defender | угроз не найдено в ZIP и распакованном каталоге; оба запуска завершились с кодом 0 |

Размер и локальный SHA-256 в точности совпали с метаданными asset в публичном GitHub API. Архив и распакованная копия находятся в исключённом из Git каталоге `artifacts/`; бинарники EMF не входят в репозиторий проекта.

Выбран именно manual-пакет. Полный `EMF-0.3.2.zip` содержит дополнительный менеджер `EMF.exe` и WebView2-интерфейс, которые для первого испытания Lua Body Adapter не нужны. Creature packs также не нужны для штатного `Enemy_Vukah_Melee`.

## Официальные источники и происхождение

Основной upstream — [репозиторий matenm/emf-enshrouded](https://github.com/matenm/emf-enshrouded). Тег `v0.3.2` является lightweight tag и указывает на commit [`08d600155fcadc8e45cc9c6f3932a67c717345be`](https://github.com/matenm/emf-enshrouded/commit/08d600155fcadc8e45cc9c6f3932a67c717345be). Публичный [GitHub Actions run для тега](https://github.com/matenm/emf-enshrouded/actions/runs/40699278069) завершился успешно. Workflow на этом commit собирает MSVC x64, запускает unit/package tests, создаёт оба ZIP и передаёт полученный artifact release job.

Дополнительные доказательства связи архива с этим исходным кодом:

- `VERSION` в pinned source равен `0.3.2`;
- в `emf_core.dll` присутствуют встроенные строки `emf_core 0.3.2`, маркер загрузчика и запись для build `1273043`;
- `dinput8.dll` содержит ожидаемый маркер `EMF-LOADER-7d3c9f`;
- `install.ps1`, `uninstall.ps1` и `emf_common.ps1` побайтно совпадают с файлами commit `08d6001`;
- `emf_bridge.py`, `emf_mcp.py` и `emf_scenario.py` побайтно совпадают с pinned source;
- структура manual-пакета соответствует [`scripts/package.ps1`](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/scripts/package.ps1): пакет создаётся из полного дистрибутива удалением `EMF.exe` и UI;
- workflow содержит package test, который отдельно проверяет manual ZIP, отсутствие `EMF.exe`, обязательные runtime-файлы и установочные сценарии.

Эти факты дают прослеживаемое происхождение release asset, но не являются воспроизводимой сборкой и не доказывают побайтовое соответствие DLL исходникам. GitHub artifact attestation для SHA-256 архива через публичный API не найден (HTTP 404), Authenticode-подписей у PE-файлов нет, локально пересобрать DLL и сравнить их побайтово не удалось. Совпадение номера `0.3.2` само по себе в выводе не использовалось.

Второй официальный канал — [EMF на Nexus Mods](https://www.nexusmods.com/enshrouded/mods/246), вкладка [Files](https://www.nexusmods.com/enshrouded/mods/246?tab=files). Там опубликованы пакеты 0.3.2 от того же автора, однако оба основных архива на момент проверки помечены как quarantined / `Some suspicious files`. С Nexus ничего не скачивалось: авторизация и ограничения сайта не обходились.

## Предупреждение Nexus Mods

Страница Files показывает для полного и manual-пакета карантин, но без входа не раскрывает конкретные названия детектов и полный отчёт сканеров. Согласно [справке Nexus о карантине](https://help.nexusmods.com/article/117-why-has-my-mod-been-quarantined), такой файл ожидает ручной проверки. [Описание статусов сканирования Nexus](https://help.nexusmods.com/article/128-anti-virus-false-positives) также не позволяет трактовать красный статус как доказательство ни вредоносности, ни безопасности.

В [публикациях автора](https://www.nexusmods.com/enshrouded/mods/246?tab=posts) предупреждение объясняется DLL-proxy/hooking через `dinput8.dll` и отсутствием подписи у `EMF.exe`. Это правдоподобно для архитектуры EMF, но является объяснением автора, а не независимым результатом анализа. Точный отчёт VirusTotal по проверенному SHA-256 в открытой выдаче не найден; поэтому конкретные детекты Nexus остаются непроверенными.

Проверенный manual-пакет отдельно просканирован Microsoft Defender:

| Параметр | Значение |
|---|---|
| Antivirus | Microsoft Defender, включён |
| Real-time protection | включена |
| Platform | `4.18.26100.4` |
| Signatures | `1.463.34.0`, обновлены 2026-10-30 03:38:30 |
| ZIP | no threats, exit code 0 |
| Распакованный каталог | no threats, exit code 0 |

Один чистый результат Defender снижает риск, но не заменяет подробный отчёт Nexus, проверку несколькими движками, анализ поведения или цифровую подпись.

## Состав и статический анализ

Архив прочитан и распакован только в отдельный каталог проекта после проверки путей. Не обнаружено абсолютных путей, `..`, drive-prefix, управляющих символов или дубликатов имён без учёта регистра. Вложенных архивов нет.

В корне находятся `install.cmd`, `install.ps1`, `uninstall.cmd`, `uninstall.ps1`, `emf_common.ps1`, документация, SDK, примеры, шаблоны, исходники/готовые пакеты модов, `game/` и диагностическая утилита `tools/emf_sigcheck.exe`. Неожиданного MSI/инсталлятора нет. Manual-пакет не содержит `EMF.exe`.

Найдено 16 PE-файлов: 15 DLL и `tools/emf_sigcheck.exe`. Все они:

- x64 (`IMAGE_FILE_MACHINE_AMD64`, `0x8664`);
- PE32+ (`0x20b`);
- без Authenticode-подписи (`NotSigned`);
- не запускались в ходе аудита.

Статические imports ограничены системными DLL Windows: `ADVAPI32`, `bcrypt`, `IMM32`, `KERNEL32`, `ole32`, `SHELL32`, `USER32`, `WINHTTP`. Delay imports отсутствуют. Не найдена статическая зависимость от отдельного Visual C++ runtime или другой DLL, которую пришлось бы доставлять рядом. Это не исключает динамическую загрузку библиотек во время работы. `WINHTTP.dll` импортирует только отключённый по умолчанию мод `herald.dll`; он не нужен нашему испытанию.

### SHA-256 PE-файлов

| Файл | SHA-256 |
|---|---|
| `game\dinput8.dll` | `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee` |
| `game\emf\emf_core.dll` | `3b2b3ddd4c3a9696dd69389ba49d33af5b5f9d1377ed44bde3cd2a73778417f3` |
| `game\emf\mods\lua\lua.dll` | `e12342a5e4b61355cf8665d4179572d3da684cc61fb4902c38de9fb4bcc28fef` |
| `game\emf\mods\companion\companion.dll` | `c659d46ce650ee4bec59cd0f72f59dbc262437583b2c759779696311ce26f979` |
| `game\emf\mods\big_stacks\big_stacks.dll` | `1b78e4107a7529c5f940c05ed7ed920bb81a0af1610e5a174d71dfa6cc820260` |
| `game\emf\mods\bulk_craft\bulk_craft.dll` | `97773021fbd5709ebc652e681ed7b2620deb071344cb4c93497f2f44ee5aa40f` |
| `game\emf\mods\clock\clock.dll` | `a8120042f381a80d200e175b14ac4defaee6ce25f78f83a53cce91aede3c5c11` |
| `game\emf\mods\herald\herald.dll` | `70693d34e4637e1846ea0747c3dbdcef5eb68d89858ce65be37f459ace09b112` |
| `game\emf\mods\loot_magnet\loot_magnet.dll` | `1c63ade360d09bb0e973b52cda01aca70c4633e15971551bcedf602ac557f987` |
| `game\emf\mods\loot_scale\loot_scale.dll` | `dbc81e0cbdf5c7bb4a72d2e975a01543e3140f9ee6afc783a82c4bb6d16b516d` |
| `game\emf\mods\quick_stack\quick_stack.dll` | `396c6ebcdc3548f880ce6fb1220de5aeac5ac6d3e31291a9b5fa4d5ed0bb2bed` |
| `game\emf\mods\raids\raids.dll` | `15be0b003cc77407fd2b008c7e7bb9a7116265d30c6cfbf56d3fef3cad491c40` |
| `game\emf\mods\sleep\sleep.dll` | `aeb12714e639c4283740942e6e81700ea1a56dbf01551a9c0c6bdf84fdf1a545` |
| `game\emf\mods\teleports\teleports.dll` | `60d81e4b7585b347355f18ae6e606b3419bb02c4b4a83f98b98d132167f1a112` |
| `game\emf\mods\villager_jobs\villager_jobs.dll` | `517068f7f0251958b753714d5619cd5a0d4e8dba1bd6e280a5968fb1dc759ac2` |
| `tools\emf_sigcheck.exe` | `a25e7bb58c4221b6629b5deec1371ccf715ec970ed9cdc94d7cba79d8ec982a7` |

`companion.dll` в архиве — штатный Companion EMF, а не наш `aic_body`. Для первого испытания его следует оставить выключенным.

### Скрипты, сеть и права

Текстовый поиск всех PowerShell/CMD/Python/Lua-файлов не нашёл загрузчиков по HTTP, BITS, `curl`/`wget`, создания служб, Scheduled Tasks, Run/RunOnce persistence, изменений Defender/firewall или сетевых установочных действий. Установочные скрипты не запускаются автоматически.

`install.cmd` явно вызывает PowerShell с `-ExecutionPolicy Bypass`; это происходит только при ручном запуске CMD-файла. План ниже использует прямой запуск проверенного `install.ps1`, поэтому обход policy не требуется. Сам `install.ps1`:

- находит игру через Steam или принимает явный `-Game`;
- перед изменениями пытается создать starter backup сохранений в `%LOCALAPPDATA%\EMF\save-backups`;
- копирует содержимое `game/`, причём `dinput8.dll` последним;
- при наличии чужого `dinput8.dll` переименовывает его и ведёт chain/rollback records;
- пишет `emf\installed.txt`;
- не скачивает файлы и не создаёт автозапуск.

Права администратора в скрипте не запрашиваются. Запись в каталог игры зависит от ACL конкретной Steam Library; текущий каталог на `D:` обычно доступен владельцу, но это будет проверено только на этапе установки. Скрипт нельзя запускать повышенно без необходимости: игра, Steam, EMF и Python bridge должны работать от одного Windows-пользователя и с одинаковым уровнем прав.

`uninstall.ps1` умеет удалять установленные файлы, восстанавливать переименованный proxy и при `-All` чистить часть пользовательских данных. В manual-сценарии нет менеджера `EMF.exe`, поэтому ветки освобождения `nxm://` не должны понадобиться. Этот скрипт также не запускался.

## Совместимость

### Enshrouded

| Проверка | Результат |
|---|---|
| Установленный EXE | `D:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe` |
| Размер | 35 338 312 байт |
| SHA-256 | `d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882` |
| Внутренняя сборка по таблице EMF | `1273043`, client x64 |
| Steam BuildID | `26082781` |
| Итог | точное совпадение с поддерживаемым client hash в `src/common/signatures.cpp` commit `08d6001` |

Steam BuildID и внутренняя сборка `1273043` — разные идентификаторы. Главным доказательством совместимости является точное совпадение SHA-256 EXE с [таблицей EMF](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/src/common/signatures.cpp#L11-L15). После любого обновления игры хеш требуется проверить заново.

Это подтверждает, что EMF 0.3.2 знает установленный EXE. Только запуск игры сможет подтвердить фактическую загрузку proxy/core, корректность сигнатур функций и отсутствие конфликта с Vulkan/оверлеями/другими DLL.

### Lua Body Adapter и Python Bridge

- `aic_body` требует EMF API `20` и Lua host `>=1.8`;
- архив содержит `lua.dll` версии `1.9.0` с `emf: 20`;
- `aic_body` выключен по умолчанию и не делает автоматический spawn;
- архив адаптера `dist/aic_body-0.1.0.zip` имеет SHA-256 `c40603f062b6a55b2a3c79fb31cfee4172a8f26f93ed676d23cc33450c8c3e91`;
- Python bridge-файлы в дистрибутиве совпадают с исследованным commit; наш клиент использует тот же named-pipe протокол;
- bridge в EMF выключен до явного `bridge=1`, поэтому сетевой listener не появляется автоматически;
- наш Body Adapter остаётся Lua-модом; собственной DLL у него нет и для этой архитектуры она не нужна.

Статическая совместимость подтверждена. Фактическое подключение named pipe, загрузка `aic_body`, доступность API в callback и игровые команды ещё не проверялись.

## Сравнение с предварительным планом этапа 3

Ожидания в [STAGE3_PREFLIGHT.md](STAGE3_PREFLIGHT.md) подтвердились:

| Ожидалось | Найдено в архиве |
|---|---|
| `game\dinput8.dll` | да, x64, unsigned |
| `game\emf\emf_core.dll` | да, встроенная версия 0.3.2/API 20 |
| `game\emf\known_tools.txt` | да |
| `game\emf\vk\VkLayer_EMF_console.json` | да |
| `game\emf\mods\lua\lua.dll` | да, Lua Scripts 1.9.0 |
| `game\emf\mods\lua\mod.json` | да, `emf=20` |
| Bridge tools | да, `emf_bridge.ps1/.py`, `emf_mcp.py`, `emf_scenario.py` |
| `EMF.exe` в manual-пакете | отсутствует, как ожидалось |
| Creature packs | отдельный optional asset, не скачивался |

Для штатной установки EMF нужен весь каталог `game/`, а не выборочная смесь DLL. Официальный `install.ps1` копирует его целиком и сохраняет список установленных файлов. Из него для работы нашего сценария критичны loader/core, Vulkan manifest, `known_tools.txt`, Lua host/manifest и bridge tools. Другие bundled-моды попадут в каталог при штатной установке, но для первого теста должны быть выключены; в частности, штатные `companion`, `clock`, `quick_stack`, `herald` и все игровые моды кроме `lua` и `aic_body`.

Не следует копировать в каталог игры вручную:

- корневые `docs/`, `sdk/`, `examples/`, `template/`, `template_lua/`, `content/`, `licenses/`, `mods/` и `tools/emf_sigcheck.exe` — это материалы для разработчика вне runtime `game/`;
- `install*.ps1/.cmd`, `uninstall*.ps1/.cmd` и `emf_common.ps1` в корень игры; штатный installer сам помещает нужные setup-копии под `emf\setup`;
- полный пакет с `EMF.exe` и UI;
- creature packs;
- штатный `companion.dll` вместо нашего Lua-мода;
- `.tools`, `.venv`, `Lupa`, каталог `companion/` или весь проект в папку игры;
- содержимое `artifacts/` и сам ZIP EMF;
- бинарники EMF в GitHub проекта.

Python-клиент, личность и runtime-логи остаются в `C:\Enshrouded-ai-companion`.

## План установки после отдельного разрешения

Ни один шаг этого раздела во время аудита не выполнялся.

1. Повторно проверить SHA-256 `enshrouded.exe` и архива. При несовпадении остановиться.
2. Дождаться завершения Steam Cloud, полностью закрыть игру, сервер и Steam.
3. Выполнить подготовленный `scripts/backup.py` с конфигурацией `config/first-test-backup.json`; продолжать только при `verified=true` и сохранённом `manifest.json`.
4. Ещё раз проверить, что в игре нет неожиданного `dinput8.dll` или другого mod loader. Если есть, отдельно проверить chain plan до изменения файлов.
5. Из распакованного официального manual-пакета запустить проверенный PowerShell-скрипт с явным путём и остановкой при неудаче starter backup:

   ```powershell
   powershell -NoProfile -File .\install.ps1 `
     -Game 'D:\SteamLibrary\steamapps\common\Enshrouded' `
     -IfBackupFails Stop
   ```

6. Сверить установленные `dinput8.dll`, `emf_core.dll` и `lua.dll` с хешами этого отчёта; сохранить `emf\installed.txt`.
7. Установить только четыре файла `aic_body` под `emf\mods\aic_body`, без двойной вложенности каталога.
8. Оставить включёнными только `lua` и `aic_body`; отключить bundled-моды, включая штатный `companion`, `clock` и `quick_stack`.
9. Включить bridge и подробный bridge log в `emf_core.ini`, не создавая `bridge.txt` вручную.
10. До spawn запустить только диагностику загрузки и подключения по инструкции этапа 3. Игровой spawn требует следующего отдельного решения после проверки логов.

## План отката после отдельного разрешения

1. Закрыть игру, дождаться Steam Cloud и выйти из Steam; отдельно сохранить диагностические логи и текущее тестовое состояние.
2. Запустить проверенный `uninstall.ps1` с явным `-Game`, сначала без `-All`, чтобы сохранить настройки/профили и не затронуть дополнительные пользовательские данные.
3. Проверить, что EMF loader удалён, ранее переименованный чужой `dinput8.dll` восстановлен, а посторонний новый proxy не перезаписан.
4. Удаление `aic_body`, его lock или восстановление сохранений выполнять только по отдельному плану с учётом состояния тела. Неподтверждённую сущность автоматически не удалять.
5. Если потребовалось восстановление мира, использовать только проверенную резервную копию и согласованный список файлов. Steam Verify не считается полным uninstall: добавленные файлы он может оставить.

## Оставшиеся риски

- Nexus не предоставил доступный гостю детальный отчёт с названиями детектов; карантин всё ещё активен.
- Все PE-файлы unsigned; у release asset нет найденной GitHub attestation.
- Бинарники не пересобирались воспроизводимо из source, поэтому полная source-to-binary identity не доказана.
- Статический import-анализ не видит runtime hooking, динамический `LoadLibrary`, сетевое поведение отключённых модов и действия после загрузки в игру.
- Defender — один антивирусный движок; его чистый результат не является гарантией безопасности.
- Совместимость подтверждена таблицей хеша, но реальная загрузка DLL, работа Lua host/bridge и поведение `Enemy_Vukah_Melee` не проверялись.
- Возможны конфликты с существующими proxy DLL, overlays, антивирусом или ACL каталога Steam; установочный path ещё не выполнялся.
- Резервная копия игры и сохранений пока не создана.

Следующий допустимый этап — **резервное копирование и отдельное ревью конкретного installation plan**. Установка, запуск игры и spawn остаются за пределами данного разрешения.
