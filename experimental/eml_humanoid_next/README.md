# Подготовка patch 0.5.0 — Stage 10.10

Это библиотека предварительной проверки, а не готовый мод. `mod.json`, регистрация
ресурса и автоматическая загрузка отсутствуют. Ничего из этого каталога не копировать
в игру. Исторический patch 0.4.0 сохранён в `experimental/eml_humanoid`.

`compatibility_guard.lua` использует подтверждённые EML 0.2.0 `game.version`,
`game.assets.get_resource`, `get_resources_by_type` и доступ к typed `.value`.
Проверяет build, source, GUID/npcId collision, состав компонентов, девять HashKey32,
animation graph и ссылки на зависимости. Возвращает только прочитанный source;
не создаёт/изменяет ресурсы, сущности и файлы.

Текущий профиль 1287369 не содержит подтверждённого clean baseline. Его нельзя
считать прошедшим эту проверку. Fixture с `clean_baseline_verified=true` в тестах
проверяет алгоритм, а не реальную базу игры. Этот флаг сам по себе не доказательство:
будущий упаковщик обязан привязать его к EXE, clean KFC/resources/DAT и manifest SHA.

До выпуска 0.5.0 нужны clean database, проверенный полный dependency manifest,
скан коллизий, выбор единственного content loader и согласованный путь evidence.
Для интегрированного EMF content требуется отдельное решение: он выключает EML
export, а patch 0.4.0 пишет evidence через `io.export`. Writer finalization нельзя
подтверждать возвратом из patch. Подробности: `docs/STAGE10_10_TEMPLATE_COMPATIBILITY.md`.
