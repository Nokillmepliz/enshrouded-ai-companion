# Stage10.10.1 Phase C — разрешённая очистка завершена

2026-11-18, завершение post-audit11:21:47UTC. Вердикт **READY_FOR_MANUAL_STEAM_VERIFY**.
Это готовность к ручному Steam repair, а не подтверждение чистого baseline или готовности установки.

Пользователь разрешил30 mod artifacts из residual-proposal и отдельно удержание
`enshrouded.kfc.bak` в новом карантине. Оригинальный KFC не восстанавливался из `.bak`.
Reviewed commit `b608cefe376b7a267a67f8b1cb9fdda579d51d6c`, proposal SHA-256
`6e7f462af6ee5d15f0fed6d4eb9b14b06c25f0603dfdcfca2f8456ca5eda6445`.
Исторический proposal не переписывался; разрешение записано отдельным operation record.

## Выполнено и проверено

| Проверка | Результат |
|---|---|
| Game/server перед переносом и после аудита | Процессы отсутствуют |
| Game/Steam identity |1287369 /26430625, depot7226436020230696061; EXE SHA совпал |
| Steam activity | Manifest StateFlags4, download/stage counters завершены; Verify не запускался |
| Dry-run |168 game,23 LOCAL,31 выбранный файл,22056395 bytes; PASS |
| Новый карантин |31/31 payload SHA/size совпали до удаления исходных имён и после переноса |
| Full post-inventory |168→137 game files; удалённые пути точно равны31 разрешённому |
| Другие изменения в game | ADDED0, CHANGED0; все137 оставшихся paths/SHA/size/mtime неизменны |
| Остаточные KEEP |20/20 без изменений |
| DAT |64/64 без изменений, включая055–063 |
| LOCAL saves |23/23 paths/SHA/size/mtime без изменений |
| Старый backup |209/209 payload SHA/size повторно проверены до и после; всё дерево сохранено |
| Старый карантин |81/81 payload и прежний журнал сохранены; всё дерево без изменений |
| Новые backups | Не создавались; создан только дополнительный карантин |

Новый карантин:
`C:\Enshrouded-ai-companion\runtime\quarantine\stage10-10-1-phase-c-20261118T1122Z`.
Payload31 файла /22056395 bytes; вместе с proposal/authorization/journal/receipt —
35 файлов /22115563 bytes. Каталог не очищается и не публикуется в GitHub.

Журнал62 записи: сначала31 `COPIED_VERIFIED_SOURCE_PRESENT`, затем31 `QUARANTINED`.
SHA-256 `ebacb25843d035858ec563b0d65f54cd61abcebf97fc4120856eda677e7424d8`.
Receipt SHA-256 `2fbd68b5394c03256d7aaa4109b6dae14591e0ff8e9580e692e5e17a890385ad`.
Raw before/after и history inventory:
`runtime/stage10_10_1_phase_c_cleanup/20261118T1122Z-execute/`.
[Публичный operation receipt и точный delta](../compatibility/recovery/1287369/phase_c/cleanup-operation.json).

Сохранены прежние папки:

- `runtime/backups/stage10-10-1-phase-b-20261118T1035Z` —420406619 bytes;
  manifest SHA `67a542553c82328bcdd589a1f4067c034bf0315fa8e375dd5a89b341c177333b`.
- `runtime/quarantine/stage10-10-1-phase-b-20261118T1035Z`;
  journal SHA `27a3a7b79a590e692c14584d1106a3a4f20112e2f26cad005a32abb1e52237d9`.

## Ограничения и исполнение

Использован отдельный [Phase C CLI](../scripts/stage10_10_1_phase_c_cleanup.py)
и [bounded executor](../companion/residual_quarantine.py). CLI по умолчанию dry-run,
проверяет pinned raw proposal и git snapshot, полный inventory, build/Steam/process state,
backup и старый карантин. Для исполнения обязательны оба явных authorization flags.
Сначала все31 копии проверены, затем перед каждым unlink повторно сверяются
source/backup/quarantine SHA и live state. Новые paths проверяются на containment,
overlap/reparse/hardlink. Рекурсивного удаления/восстановления/автопродолжения нет.

Старый recovery CLI продолжает запрещать KFC.bak; его политика не ослаблена.
Новый scope допускает только точный `enshrouded.kfc.bak` как отдельно разрешённое удержание.
Это не доказательство vanilla provenance. Исходные EXE/KFC/resources остались прежними:

| Файл | SHA-256 до и после |
|---|---|
| enshrouded.exe | `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77` |
| enshrouded.kfc | `bf19e811565e5f6d68bc88979f8d397c0fbd069777445acf02ab882879699c39` |
| enshrouded.kfc_resources | `8bfe6a11062d711f363389e744ee3cf43ab0c727a9480fe199b673595fdedcb4` |

Индекс остаётся mixed, старый clone пока не опровергнут. DAT055–063 не переносились
и требуют анализа после Steam Verify. Все20 KEEP сохранены:9 DAT,3 vendor DLL,
settings JSON и7 исторических diagnostic files. Пустые директории оставлены на месте.
SHA-проверки не являются атомарной блокировкой от внешнего привилегированного writer;
поэтому перед будущими действиями снова требуется свежий preflight.

## Тестирование и следующий шаг

12 новых fixture tests PASS: exact31/20KEEP, отдельное согласие .bak, changed source/
backup/build/inventory/LOCAL, protected targets, duplicate/overlap/hardlink, copy failure,
partial unlink failure с сохранёнными копиями/журналом и запрет повторного запуска.
Полный suite:631 testsRun /630 PASS /1 прежний skip /0 failures.
Python compileall, git diff check и Lua syntax15/15 PASS. Rust/C++ не менялись и
не перезапускались. Фикстуры не содержат игровых ресурсов и не запускали игру.

Теперь пользователь может выполнить [Steam Verify вручную](STAGE10_10_1_STEAM_VERIFY_PLAN.md),
дождаться завершения и сообщить результат. Игру не запускать. После сообщения продолжить
post-Steam Phase C/D по уже полученному ТЗ: fresh build/inventory, Inspector source/clone/
visual audit, clean acceptance, verified clean backup, затем migration package.
Ограниченный backup не позволяет гарантированно вернуть все DAT к mixed state;
полная52GB копия по решению пользователя не создавалась. Объём скачивания Steam неизвестен.

`steam_verify=NOT_EXECUTED`, `clean_baseline_confirmed=false`,
`installation_authorized=false`, `installation_executed=false`,
`runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
