# Stage 10.10 — стратегия перехода, без выполнения

Текущее состояние: EXE1287369, старые EMF/EML/patch files, modified KFC с custom
GUID, EMF0.3.2 idle. Verdict **BLOCKED_BY_GAME_INTEGRITY**, дополнительно EML/evidence
integration и clean-resource schema acceptance не завершены. Не устанавливать
EMF0.6.18 поверх этой смеси автоматически.

| Сценарий | Допустимая будущая стратегия |
|---|---|
| EMF и EML подтверждены для нового build | review конкретных hashes/единого content owner → отдельное разрешение Phase B → load-only Phase C |
| Только EMF поддерживается | read-only source/EXE/Bridge contract research; template patch заблокирован |
| Только EML поддерживается | можно предложить отдельно разрешённый EML-only load test; Bridge/observer gates не выдавать за PASS |
| Ни один не поддерживается | ничего не устанавливать; искать upstream fix/официальный release, продолжать offline tests |
| Игра остаётся 1273043 | сохранить старый профиль; не инициировать Steam update |
| Остались mod artifacts | exact cleanup candidates + новый current-state backup; удаление только после отдельного согласования |
| Mixed/unknown game data — наш случай | сначала сохранить текущее состояние; отдельно согласовать получение clean Steam baseline; старый restore запрещён |

Для clean baseline возможен пользовательский Steam Verify Integrity после
отдельного разрешения. До него сохранить текущие ресурсы, установленную конфигурацию
и LOCAL saves. Verify может заменить данные игры, но не гарантирует удаления чужих
DLL/mod folders. Поэтому после него нужен новый полный inventory, отсутствие
clone GUID в базе, повторный source/dependency/collision audit и проверка
отсутствия вмешивающегося loader. `.bak` не принимать за clean только по имени.

Две альтернативы content owner:

1. Standalone EML0.2.0 с текущим export workflow: минимум переноса evidence, но
   пишет игровые KFC/resources и требует актуальной binary/runtime проверки.
2. EMF0.6.18 `emf_content.dll` shadow workflow: базовые игровые данные upstream
   заявляет неизменяемыми, но standalone dbghelp должен отсутствовать; наш export
   evidence workflow надо адаптировать и проверить, не подменяя его логом writer.

Выбор требует готового reviewable patch/observer и конкретного нового install plan.
Сейчас ни одна альтернатива не объявлена готовой. Сохранения не восстанавливать из
старой копии и не считать их совместимость проверенной без ручного запуска;
новая игра может мигрировать их при первом открытии.

Для Stage 11.0 после Stage 10.10 Phase D: закрепить новый profile/EXE/content
baseline, использовать upstream ground/path/villager_move, удалить дублирующую
разработку этих функций из scope; отдельно решить instance identity, ownership,
atomic destroy, capsule clearance и unique villager persistence. Не переносить
старые offsets, 81 components и 412d61b0. Любой spawn требует нового разрешения.
