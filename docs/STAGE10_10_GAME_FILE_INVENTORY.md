# Stage 10.10 — read-only inventory

Дата: 2026-11-18. Полностью прочитаны и хешированы **249 файлов игры и 23 LOCAL-файла**.
Начальный снимок сохранён в ignored `runtime/stage10_10/before.json`.
Публичный список с размером, SHA-256, прежним SHA и статусом:
[file-inventory.json](../compatibility/audits/1287369/file-inventory.json).

| Категория | Количество | Значение |
|---|---:|---|
| UPDATED_BY_GAME | 1 | EXE: новый build и известный upstream fingerprint |
| PREVIOUS_MOD_ARTIFACT | 19 | 9 receipt files + 9 пустых DAT + старый EMF loader с прежними хешами |
| MODIFIED_UNKNOWN | 28 | KFC/resources/.bak и 25 исходных DAT изменены; нет доверенного нового per-file depot baseline |
| UNCHANGED | 30 | 30 исходных DAT совпадают со Stage 10.7 |
| NEW | 171 | нет прежнего индивидуального digest в Stage 10.7; не означает, что файл создан только сейчас |
| MISSING | 0 | среди путей, для которых есть прежние индивидуальные хеши |

Stage 10.7 не содержал полного снимка всех файлов игры. Поэтому нельзя объявить
171 файл реально новым или приписать их Steam. Среди них есть старые логи,
EMF и `.cache/export/logs`; их принадлежность по одному имени не доказана.

| Файл | SHA-256 сейчас |
|---|---|
| enshrouded.kfc | `bf19e811565e5f6d68bc88979f8d397c0fbd069777445acf02ab882879699c39` |
| enshrouded.kfc_resources | `8bfe6a11062d711f363389e744ee3cf43ab0c727a9480fe199b673595fdedcb4` |
| enshrouded.kfc.bak | `2093a7cc0859ba2f878fc252a65c36b39605d7e1106e091c63809f6dea460bf5` |
| dinput8.dll — установленный EMF 0.3.2 | `53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee` |
| dbghelp.dll — установленный EML 0.2.0 | `038b7a1787026007a68c82a6adeb8e79c2e644f936d4cd00f8b0db206a2349fa` |

Все 9 файлов receipt Stage 10.7 по-прежнему совпадают. В игре остались patch 0.4.0,
read-only observer, старые EMF-компоненты и настройки Bridge (`bridge=1`).
Включённость отдельных старых модов не означает успешную загрузку: сохранённый
лог EMF от 6 ноября сообщает `38 of 50 usable`, `EMF stays idle, no mods loaded`.
Это **исторический лог**, не запуск Stage 10.10.

DAT 055–063 по 0 bytes, каждый SHA
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Совпадение со старым EML output фиксируется, но не резервирует эти номера за модом.
Удалять их на новой сборке без нового плана и атрибуции нельзя.

В KFC найден custom GUID; source и clone имеют уже по 82 компонента.
Поэтому `clean_baseline=false`, verdict **BLOCKED_BY_GAME_INTEGRITY**.
`.bak` тоже новый и отличается от исторической копии; его чистота не установлена.
[Cleanup candidates](../compatibility/audits/1287369/cleanup-candidates.json) — перечень
для обсуждения, **не исполняемый план удаления**. Текущие файлы сохранены.
