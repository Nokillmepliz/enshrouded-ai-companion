# Stage10.10.1 Phase D — независимая подготовка до clean baseline

2026-11-18. Вердикт **MIGRATION_PACKAGE_PARTIAL**. Дополнительный карантин31 файла
разрешён и выполнен; [контрольный аудит](STAGE10_10_1_PHASE_C_CLEANUP.md) завершён.
Ручной Steam Verify завершён; новый [post-Steam аудит](STAGE10_10_1_POST_STEAM_AUDIT.md)
подтвердил61/61 depot file, отсутствие clone GUID/npcId,82 source components,
18 visual references и102 joints. Формальный baseline PARTIAL: локальный depot cache
не содержит проверенной подписи; ограниченное acceptance предложено пользователю.
Независимая офлайн-работа выполнена; финальная сборка patch/resource contract
зависит от принятия нового baseline.

## Что подготовлено

- Read-only shadow integrity validator с реальными filesystem fixtures;
  [контракт и ограничения](STAGE10_10_1_SHADOW_INTEGRITY.md).
- [Reproducible component staging helper](../scripts/prepare_integrated_components.py):
  pinned archive digest, exact member allowlist, повторные hashes, x64 PE inspection,
  exclusive output только под project/dist. Архив не распаковывается целиком.
- Локальная staging-папка **`C:\Enshrouded-ai-companion\dist\stage10_10_1_integrated_components_20261118_r2`**:
  8 кандидатов в игру и12 лицензий/уведомлений. Это не backup и не install receipt.
  Первая staging-ревизия заменена кандидатом r2 после исправления INI-секции на `[lua]`;
  для review используется только r2. Никакие staging-файлы не загружались как код.
- [Component manifest](../compatibility/migration/1287369/component-candidate.json)
  содержит source/destination, размеры, hashes, imports и повторный Authenticode result.
  `complete_migration_package=false`; никакие копирования в игру не разрешены.
- [Clean candidate configs](../experimental/integrated_content/emf_core.ini):
  `[content] mode=on, log_opens=1`; `[debug] bridge=1, bridge_verbose=1`.
  Lua enable задаётся в `[lua]`, по SettingsStore/backend источника.
  Старые23 configs нельзя наследовать. `mode=on` не отменяет проверку другого owner.
- Профиль1287369 фиксирует выбранный `EMF integrated content`; индекс его raw SHA
  обновлён. Clean metadata/patch остаются незаполненными, installation_ready=false.
  Исторический профиль1273043 и patch0.4 не изменены. Поле eml_sha256 в старом candidate
  описывает исторический standalone binary; его нельзя использовать для установки
  integrated content — pinned content DLL указан в новом component manifest.

## Минимальный компонентный allowlist

| Будущий путь в игре | Назначение |
|---|---|
| dinput8.dll | EMF loader |
| emf/emf_core.dll | Core API46 / Bridge protocol1 |
| emf/emf_content.dll | Integrated vendor EML0.2.0 |
| emf/mods/lua/lua.dll | Lua host1.39.0 |
| emf/mods/lua/mod.json | Обнаружение host |
| emf/known_tools.txt | Классификация других loaders/tools |
| emf/emf_core.ini | Новая конфигурация content/Bridge |
| emf/config/lua.ini | Новая конфигурация host |

12 license/notice files остаются в package, не копируются в game paths.
В staging нет installer/uninstaller, manager EXE, Companion, Beastmaster, Villager Jobs
или legacy AIC Body. Официальный архив целиком содержит дополнительные компоненты,
но в allowlist они не вошли.

Release asset SHA `12bbcae2e52386bcd7f1747701bb6d1ec8a64fab061e6e33ce994b6ee29c926b`
заново совпал с [GitHub asset digest](https://github.com/matenm/emf-enshrouded/releases/tag/v0.6.18).
Все4 DLL повторно: x64/PE32+, Authenticode NotSigned. Imports — системные Windows DLL;
статический список не исключает dynamic loading. Binary/source reproducibility,
runtime совместимость и отсутствие вредоносного поведения этим не доказаны.
Ни DLL, ни EXE из архива не запускались; антивирус не отключался.

## Что ещё не готово

| Результат ТЗ | Фактический статус / зависимость |
|---|---|
| Patch0.5.0 | PATCH_PREPARATION_ONLY; нужен authoritative clean source/clone contract и collision scan |
| Appearance/fingerprints | Исторические82/18/102 не приняты за новую clean норму |
| Evidencev8 | Имеются прежние offline emitter/parser; полный BEGIN/END и live provenance capture ещё не завершены |
| Observer package | Offline library есть; bootstrap/mod.json/live session/world binding ещё не готовы |
| Python Bridge | Protocol1 сохраняется как цель; live capture migration/fake-transport acceptance ещё не завершены; реального подключения не было |
| Compatibility profile | Candidate заблокирован clean baseline; финальный профиль после fresh resource inspection |
| A/H/R/V/B/C evaluator | Прежние gates не ослаблены; реальные runtime gates NOT_EXECUTED/UNKNOWN |
| Exact install manifest | Нет; component manifest не содержит будущий patch/observer и post-clean before hashes |
| Новый rollback dry-run | NOT_EXECUTED: нет новой полной установки/receipt; старый rollback запрещён |
| Load-only план | [Подготовлен сценарий](STAGE10_10_1_LOAD_ONLY_PLAN.md); исполнение не разрешено |

После Phase C продолжить эти пункты по тому же ТЗ. Нет основания запрашивать Phase E:
конкретный полный install/rollback plan ещё не может быть проверен на чистой базе.
После Steam добавлены read-only depot parser, полный NPC collision scan в Inspector
и исправление shadow validator для55 base DAT при64 files в корне. Исходный контракт
теперь опубликован отдельно; historical patch0.4 и blocked profile не переписаны.
Следующее действие — решение об ограниченном baseline acceptance; далее verified
backup27 файлов260563026 bytes и завершение candidate. Это план, не выполненная установка.

## Ответы на21 итоговый вопрос ТЗ

Ответы ниже относятся к pre-cleanup checkpoint. Последующее изменение:31 разрешённый
файл перенесён, осталось137 game;20 KEEP/64 DAT/23 LOCAL неизменны. Steam Verify пока
не выполнялся. Полные фактические результаты — в отчёте очистки выше.

1. Чистая игра ещё не восстановлена.
2. В этой задаче перемещено0 файлов; прежние81 находятся в карантине.
3. Все168 игровых/51 residue/64 DAT и23 LOCAL сохранены.
4. Steam Verify не выполнялся; изменений от него нет.
5. Установлен build1287369, Steam26430625.
6. Новые backups0 bytes; прежний проверенный backup420406619 bytes.
7. LOCAL23/23 сохранены; before/after сравнение отдельно опубликовано.
8. Отсутствие старого clone не подтверждено; база остаётся mixed.
9. Source hunter исторически найден; clean readback ещё не выполнен.
10.82 components — прежний mixed audit, не новый authoritative fingerprint.
11. Визуальная цепочка исторически исследована; на чистой базе ещё не проверена.
12. Patch0.5.0 не готов к установке.
13. EMF component subset готов для review; полный migration package частичен.
14. Новый installable observer не завершён.
15. Мигрированный live Bridge ещё не принят; подключения к игре не было.
16. Оригиналы проверяются полным SHA inventory и shadow validator по file identity.
17. Shadow проверяется exact allowlist, private/link roles, SHA/identity/link count;
    writer/unload/redirection/readback остаются независимыми gates.
18. Exact install manifest ещё не готов: clean baseline и AIC artifacts отсутствуют.
19. Фактические Python/Lua/static/backup результаты — в актуальном TEST_RESULTS.
20. Блокеры: дополнительный quarantine approval, manual Verify, clean resource acceptance,
    далее patch/observer/evidence/Bridge integration и exact install/rollback contract.
21. Phase E пока не готова к разрешению.

`installation_authorized=false`, `installation_executed=false`,
`runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
