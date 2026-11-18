# Stage10.10.1 Phase C — до дополнительного карантина и Steam Verify

Дата: 2026-11-18. Исходный commit: `df18d6c999f810b54706ff32570631ff30eac2f4`.
Вердикт **CLEAN_BASELINE_BLOCKED**. Выполнен повторный read-only аудит; Phase C не завершена.
Текущая контрольная точка — согласование [точного списка](STAGE10_10_1_RESIDUAL_CLEANUP_APPROVAL.md).

## Повторно проверено

- Game/server не запущены. Полный новый inventory:168 игровых и23 LOCAL-файла;
  совпали с Phase B по путям, SHA-256, размеру и mtime. Итоговый inventory после
  офлайн-работы сравнивается отдельно в `phase_c/session-integrity.json`.
- Игра1.0.1.2 / internal build1287369: EXE SHA-256
  `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77`.
  Steam build26430625, depot1203621 manifest7226436020230696061 не изменились.
- Backup209/209 payload SHA/size и карантин81/81 повторно проверены.
  Backup manifest SHA `67a542553c82328bcdd589a1f4067c034bf0315fa8e375dd5a89b341c177333b`;
  quarantine journal SHA `27a3a7b79a590e692c14584d1106a3a4f20112e2f26cad005a32abb1e52237d9`,162 записи.
- Из известных loaders отсутствуют dinput8.dll, dbghelp.dll, emf/emf_core.dll.
  При финальном install review потребуется повторный полный поиск конфликтов,
  включая auto-discovery; отсутствие этих трёх файлов само по себе недостаточно.
- [GitHub Releases](https://github.com/matenm/emf-enshrouded/releases/tag/v0.6.18)
  заново подтвердил latest EMF0.6.18. Последний найденный changelog в официальной
  [Steam feed](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1203620&count=6&maxlength=600&feeds=steam_community_announcements)
  — Hotfix5,1.0.1.2/build1287369. Новая версия не обнаружена в этих источниках;
  это не независимая проверка всех файлов установленного Steam depot.

[Проверки и identity](../compatibility/recovery/1287369/phase_c/pre-steam-review.json),
[публичные release metadata](../compatibility/migration/1287369/official-updates.json).
Raw before/after inventory хранится только в
`runtime/stage10_10_1_phase_cd/20261118_review/`.

## Текущее состояние ресурсов и post-Steam audit

Steam Verify **NOT_EXECUTED**; сообщение пользователя о завершении ещё не получено.
Новые перемещения —0. Все51 остаточных файла остаются на месте. Старый rollback не запускался.

| Объект | SHA-256 | Что установлено |
|---|---|---|
| enshrouded.kfc | `bf19e811565e5f6d68bc88979f8d397c0fbd069777445acf02ab882879699c39` | 64 containers; смешанный index |
| enshrouded.kfc.bak | `2093a7cc0859ba2f878fc252a65c36b39605d7e1106e091c63809f6dea460bf5` | 55 containers; не доверенный baseline |
| enshrouded.kfc_resources | `8bfe6a11062d711f363389e744ee3cf43ab0c727a9480fe199b673595fdedcb4` | SHA неизменен; чистота не подтверждена |
| DAT000–063 | все64 SHA/size/mtime неизменны | DAT055–063 пустые; принадлежность не установлена |

В обоих KFC тот же полный build string1287369. По pinned `choose_base` сейчас
выбиралась бы `.bak`; это вывод из source, не запуск loader. `.bak` не восстанавливаем
поверх KFC. Номер/пустой SHA DAT не доказывает принадлежность моду.

Историческое обнаружение clone `a1c90001-5e4d-4a91-8a1c-000000000001` относится
к этой hash-неизменившейся смешанной базе. Нового декодирования/проверки отсутствия
clone на чистой базе пока нет. Исторические source82 components/18 visual refs/
102 joints не назначены authoritative clean fingerprints.

Новые backups: **0 bytes**. Существующий mixed backup —420406619 bytes с manifest/plan,
209 payload files плюс2 metadata files. DAT-тела отсутствуют; полный возврат mixed state
после Steam repair не гарантируется. Пользователь ранее принял это ограничение.
Verified clean backup пока не создаётся: чистой базы ещё нет.

## Контрольные точки

1. Согласовать30 перечисленных mod artifacts и отдельно изоляцию одного KFC.bak.
   Для `.bak` требуется отдельная операция сохранения в карантине; старый recovery CLI
   намеренно запрещает KFC.bak. Не обходить этот запрет редактированием старого manifest.
2. Перед фактической операцией заново проверить full inventory, backup, закрытые
   процессы, Steam identity и reviewed proposal digest. Новый журнал, новые пути,
   copy→SHA verification→source recheck→удаление только исходного имени. При ошибке
   остановиться; никаких неизвестных файлов или автоматического продолжения.
3. После разрешённой очистки и её проверки дать сигнал к ручному Steam Verify.
   Не запускать игру. [Пошаговая инструкция](STAGE10_10_1_STEAM_VERIFY_PLAN.md).
4. После сообщения о завершении: определить актуальный build, повторить full inventory,
   ADDED/REMOVED/CHANGED/UNCHANGED, отдельно residue/UNKNOWN, сравнить LOCAL.
5. На восстановленных ресурсах Inspector: KFC/DAT references, source humanoid,
   отсутствие clone GUID и npcId2939921867 collision, preset/graph/hierarchy/skeleton,
   typed HashKey32 и новая canonical identity. Ошибка lookup не считается отсутствием.
6. Применить [clean evaluator](STAGE10_10_1_CLEAN_BASELINE_CONTRACT.md).
   Без независимых depot hashes максимум PARTIAL; можно обсудить ограниченный acceptance
   с resource-level evidence. Не превращать UNKNOWN в PASS и не требовать недоступных
   upstream данных бесконечно. Только затем clean backup и завершение Phase D.

Отдельные post-Steam/clean-baseline документы пока объединены с этим отчётом:
фактического Steam repair/clean acceptance ещё нет. Phase E не готова к согласованию.

`installation_authorized=false`, `installation_executed=false`,
`runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
