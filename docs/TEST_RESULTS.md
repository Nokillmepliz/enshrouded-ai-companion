# Результаты подготовки этапа 2

## Этап 6 — Human Body research, 30.10.2026

- `.tools/python/python.exe -m unittest discover -s tests -q`: **97 тестов, PASS**.
- `.tools/python/python.exe -m compileall -q companion scripts tests`: PASS.
- `git diff --check`: PASS.
- `scripts/package.py`: архив содержит новый `body_profiles.lua`, выключен по умолчанию и воспроизводим; SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`.
- Десять новых тестов проверяют каталог human candidates, запрет runtime-выбора, capabilities, missing/partial/delayed fingerprint, reflection timeout, identity change/EntityId reuse, exact-current-observation перед удалением и изоляцию legacy Vukah GUID.
- Все прежние 87 тестов сохранены, включая partial spawn/dismiss, faction failure, unknown outcome, runtime.lock/reload и запрет удаления untrusted entity.
- Старые GUID тела/маркера вынесены в `body_profiles.lua` как `legacy_vukah`; runtime-поведение protocol 1 / `safety_revision=2` не менялось.
- Human runtime adapter, spawn, movement, inventory и equipment **не реализованы**. Тесты подтверждают fail-closed офлайн-политику, а не работу humanoid в Enshrouded.
- Игра не запускалась; файлы игры и сохранения не менялись.

## Актуальное техническое ревью — 30.10.2026

- Полный запуск `.tools/python/python.exe -m unittest discover -s tests -q`: **87 тестов, PASS** (56 прежних с уточнёнными ожиданиями и 31 новый тест).
- `.tools/python/python.exe -m compileall -q companion scripts tests`: PASS.
- `git diff --check`: PASS.
- `scripts/package.py`: ZIP пересобран; SHA-256 `c40603f062b6a55b2a3c79fb31cfee4172a8f26f93ed676d23cc33450c8c3e91`.
- Текущая ревизия безопасности адаптера: **safety_revision=2**, protocol=1. Новый Python-клиент отказывает в игровых изменениях через старую ревизию.
- В тестах используется настоящий Lua 5.4 через Lupa и поддельный EMF. Отдельно проверены реальные Lua операции с lock во временном каталоге; игровых файлов это не касается.
- Изучены локальные исходники EMF на commit `08d600155fcadc8e45cc9c6f3932a67c717345be`: нативные spawn/destroy, Lua bindings/host, EntityId, SpawnTime, StoredSceneId и перечисление WorldView. Проверяемого generation ID экземпляра для наших шаблонов не найдено; ссылки и ограничения — в [PROTOCOL.md](PROTOCOL.md).
- EMF не установлен, игра не запускалась, bridge к игре не подключался, игровые файлы и сохранения не изменялись. Игровые проверки: **NOT RUN**.

Ниже сохранена история прошлых запусков и старых хешей архива; для текущего испытания использовать результат выше.

Обновление этапа 3 от 30.10.2026: **56 тестов PASS**, `compileall` PASS. Добавлены логи клиента/адаптера и проверяемое резервирование. Текущий архив имеет SHA-256 `e9fb551e69bed8ba2f26884436b3b9c6c7b4bf4bea48df3a67d8641778e391ff`; приведённый ниже хеш относится к предыдущему архиву этапа 2. [Подробный текущий отчёт](STAGE3_PREFLIGHT.md). DLL EMF отсутствуют; в игре ничего не проверялось.

Дата: 30 октября 2026 года.

## Выполнено без игры

- `python -m unittest discover -s tests -q`: **48 тестов, PASS**.
- `python -m compileall -q companion scripts tests`: PASS.
- `python -m companion --help`: CLI доступен, подключения к игре нет.
- Проверены 87 ссылок на upstream-исходники (существование файлов и границы строк), относительные ссылки документации и отсутствие пробелов на концах строк исходников.
- `python scripts/package.py`: создан `dist/aic_body-0.1.0.zip`; тест архива проверяет состав, disabled manifest и воспроизводимость.
- Проверен SHA-256 включённого Python bridge; функционально он не изменялся.

Среда: Windows, изолированный Python 3.12.10 в `.tools/python`, Lupa 2.6 с Lua 5.4. Для Lua запускается настоящий код `main.lua`/`body.lua`/`json.lua`; EMF, файлы мода и мир подменены тестовой средой. Системная установка Python не изменялась. `.tools` исключён из Git.

SHA-256 подготовленного архива:

```text
d51908d0dc32e341f1195168df07009ed2685580dd545746acd0ff5f7e8ef00e  aic_body-0.1.0.zip
```

## Не выполнялось

Установка EMF/адаптера, включение bridge, подключение к игровому процессу, изменение файлов игры/сохранений, запуск мира, спавн реальной сущности и игровые испытания. Наличие ModelResource на выбранных теле/маркере, работа reflection на установленной версии и длительное физическое следование пока не подтверждены.

Следующий этап — [FIRST_RUN.md](FIRST_RUN.md) и [TEST_PLAN.md](TEST_PLAN.md), отдельно после подтверждения пользователя. Текущий результат подтверждает логику прототипа и его контракт, а не работу внутри игры.


## Этап 7 — Player Character Companion, 30.10.2026

- `.tools/python/python.exe -m unittest discover -s tests -q`: **110 тестов, PASS**. Сохранены прежние 97 и добавлены 13 тестов player-character policy.
- `.tools/python/python.exe -m compileall -q companion tests scripts`: **PASS**.
- `.tools/python/python.exe scripts/package.py`: **PASS**; две последовательные сборки дали одинаковый SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`.
- Новый `companion/player_character.py` — только офлайн evidence/identity/authority policy. Он не входит в Lua-архив, не подключается к игре и не включает runtime-команды.
- Read-only анализ сохранений ограничен метаданными файлов. Save-файлы, Steam ID, игровые бинарники и приватные логи в Git не добавлены.
- Игра, второй клиент, spawn, input, inventory operations и AI Brain не запускались.

## Этап 8 — Independent Humanoid, 30.10.2026

- `.tools/python/python.exe -m unittest discover -s tests -v`: **126 тестов, PASS**. Сохранены прежние 110, добавлены 16 тестов independent lifecycle, read-only policy и компиляции Lua survey.
- `.tools/python/python.exe -m compileall -q companion tests scripts`: **PASS**.
- `git diff --check`: **PASS**.
- `scripts/package.py`: **PASS**, legacy-пакет `aic_body` не изменился, SHA-256 `998bf16b03e6d7db41f5851dc51c70a840f35dab4d8796b8c4291cdb01335872`. Survey является отдельным исходным модом и в этот ZIP не включён.
- `companion/independent_humanoid.py` не подключается к игре. Все реальные descriptors уникальны и выключены; неизвестные шаблоны и операции отклоняются.
- `mods/aic_humanoid_survey` выключен по умолчанию. Статическая проверка запрещает spawn/destroy/event emission/inventory/save/tick paths; Lua syntax проверяется отдельно перед публикацией.
- Игра не запускалась, survey не устанавливался, игровые файлы/сохранения/сущности не менялись. Human spawn, movement, combat, inventory, equipment и persistence: **NOT RUN / BLOCKED**.
