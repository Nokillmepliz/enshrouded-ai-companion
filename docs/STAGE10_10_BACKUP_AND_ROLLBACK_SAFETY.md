# Stage 10.10 — backup и rollback safety

На 2026-11-18 заново проверены **317 файлов в пяти копиях**: 105/105, 144/144,
24/24, 24/24 и 20/20. [Имена и manifest hashes](../compatibility/audits/1287369/backup-audit.json).
Новые backup в Phase A не создавались. Копии сохранены без изменения manifest.

Manifest Stage 10.7 SHA-256
`7ac4df3609d2609673345d029844dcf8d9181ba768762aa6eb6b62752cb9b651` совпал
с историческим отчётом. Receipt SHA-256
`3280870774f3b0283bad0cb6e3063e03ca57f42de8de876578fdf90a269bf2e6` тоже совпал;
его 9/9 installed files проверены. Приватный token не публикуется.

У старых backup отсутствует embedded EXE/build identity. Принадлежность 1273043
устанавливается по датированным project reports и старым hashes, а не по новому
полю, добавленному задним числом. Только два упомянутых SHA имеют здесь внешнее
историческое закрепление; для прочих manifest вычислен текущий hash и проверено
содержимое, но независимый старый manifest digest не заявляется.

Раньше rollback мог удалить receipt paths без проверки EXE, а restore принимал
DAT по именам. Теперь реальные helpers в [stage10.py](../companion/stage10.py):

1. Определяют identity по точному EXE SHA; stale log не заменяет EXE.
2. Связывают новый backup с build и canonical digest KFC/resources/исходных DAT.
3. Связывают новый receipt с game identity, baseline и точным manifest SHA.
4. Не принимают legacy receipt как разрешение; сохраняют возможность его чтения.
5. До изменений проверяют весь allowlist targets, запрещают неизвестные/повторные
   пути, traversal, ADS, symlink/junction. Повторяют digest-check перед каждым действием.
6. Для restore требуют отдельный reviewed state с точным набором before hashes,
   manifest hash и baseline identity. Прежние DAT должны также совпадать.
7. Ничего не восстанавливают в LOCAL saves. Старый broad directory cleanup
   `.cache/export/logs` выведен из использования: по имени папки удалять нельзя.

Коды: `ROLLBACK_BLOCKED_BUILD_MISMATCH`, `ROLLBACK_BLOCKED_FILE_MISMATCH`,
`ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT`. Historical installer остаётся только для
1273043; он не становится новым installer от одного добавления профиля.

Проверки выполнялись на временных fixtures: successful same-build dry-run,
cross-build apply с нулём удалений, отказ старого KFC restore, повреждённый backup,
stale baseline, чужой target, дубликат, имя DAT, изменённый receipt и unsafe paths.
На **реальном каталоге** rollback/restore/dry-run destructive workflow не запускался:
его запрещает пользователь и заранее блокирует известный build mismatch.

Это контролируемый workflow при закрытых игре/сервере, не атомарная filesystem
транзакция против параллельного злоумышленника. При ошибке посреди отдельно
разрешённого применения надо остановиться, сохранить фактическое состояние и
составить новый reviewed plan; нельзя подправлять receipt вручную.

Для Phase B нужны отдельная копия **текущего** mixed state/LOCAL и позднее verified
clean backup 1287369. Старые backups допустимы как исторические артефакты,
**не как источник game-data restore поверх новой сборки**. Steam Verify не заменяет
backup и может оставить посторонние DLL; сейчас он не выполнялся.
