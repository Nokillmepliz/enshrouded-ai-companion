# Проверка private shadow — реализованная офлайн-часть

Новый [валидатор](../companion/shadow_integrity.py) только читает файлы.
Его [14 fixture-тестов](../tests/test_shadow_integrity.py) выполнены на временных
синтетических данных, включая Windows hardlinks и junction. Игровой writer не запускался.

Основание: pinned EMF0.6.18
[content_shadow.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_shadow.h),
[content_base.h](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/src/loader/content_base.h),
[vendor patches](https://github.com/matenm/emf-enshrouded/blob/fa6efdac2d93dd1d8ac6fe0e2a658140aec35241/third_party/eml/EMF_PATCHES.md).

Входы: clean baseline **до установки**, exact expected shadow allowlist после
отдельного проверенного readback и пути original/shadow. Каждый original baseline
должен иметь один link. Поддержан только reviewed client shadow
`<game>/emf/content/client`; server и дополнительные hardlinks требуют нового контракта.

| Роль | Проверка |
|---|---|
| Original EXE/KFC/resources/DAT | SHA/size/mtime, volume ID и file ID не изменились; точный resource set |
| BASE_LINK: EXE/base DAT из проверенного KFC | Тот же volume+file ID, link count2, SHA baseline |
| Unreferenced root DAT | Hash/size/identity/mtime неизменны, link count1; не считаются base links |
| PRIVATE_INDEX: KFC/resources/внутренний .bak | Отдельный file ID, link count1; ожидаемый SHA |
| GENERATED_DAT | Имя вне base DAT из KFC, private single-link, ожидаемый SHA; при совпадении имени с unreferenced root DAT file identity обязана отличаться |
| MOD_COPY/CACHE | Явные пути внутри mods/ или .cache/, private single-link и ожидаемые SHA |
| METADATA | Только shadow.txt/emf_content_state.json в exact allowlist |
| TEMPORARY/неожиданные файлы | Блокируют finalized-shadow acceptance |

Junction/symlink/reparse проверяются у файлов, каталогов и предков корня.
Traversal, ADS, абсолютные пути, Windows reserved names и case aliases отклоняются.
Originals читаются ещё раз после shadow audit, чтобы заметить изменение во время проверки.
Наличие root KFC.bak блокирует использование текущего input как доверенного clean base.

Post-Steam correction: `base_dat_count=55` получен из Inspector, хотя в корне64 DAT.
Нельзя выводить число base links из количества файлов каталога. Параметр валидатора
обязан быть привязан к проверенному KFC/run; отсутствие явного параметра сохраняет
прежний строгий режим «все DAT — base» для старых fixtures. Реальная установка должна
передавать проверенное число55. Девять пустых root DAT055–063 остаются нетронутыми;
они не запрещают одноимённые приватные outputs в отдельном shadow. Два новых теста
проверяют это различие и отказ при недопустимом container count.

Положительный fixture проверяет приватную запись KFC и unlink-before-write нового DAT.
Отрицательный fixture действительно записывает через hardlink **в искусственный файл**:
изменение original ловится как `ORIGINAL_MUTATION`. Дополнительные неизвестные ссылки,
приватный index с hardlink, совпадающие bytes при иной identity также блокируются.

Ограничения: filesystem audit не является атомарной блокировкой ОС и не защищает от
привилегированного writer между наблюдениями. Он не декодирует KFC и не доказывает,
что index ссылается только на разрешённые DAT; это отдельный Inspector/readback gate.
Список expected SHA должен быть привязан к reviewed readback/run, а не автоматически
снят с проверяемого shadow и объявлен доверенным.

Даже при `filesystem_integrity=PASS` результат сохраняет writer_completion,
redirection и resource_semantics=UNKNOWN, runtime=NOT_EXECUTED, render=UNKNOWN,
spawn_ready=false. Будущий capture обязан независимо подтвердить content state,
writer close, DLL unload, source selection, redirect log и актуальную session.
Отсутствие этих доказательств блокирует load-only acceptance; supplied fixture
или print не повышает runtime gate.
