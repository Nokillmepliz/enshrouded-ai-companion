# Stage 10.10.1 — аудит после ручного Steam Verify

Дополнение 2026-11-18: пользователь принял указанное ниже ограничение PARTIAL.
Новая clean copy27/27 создана и проверена; офлайн-Phase D завершена.
[Актуальный результат и точный install plan](STAGE10_10_1_PHASE_D_REPORT.md).
Исторические расчёт backup и PROPOSED_NOT_GRANTED ниже описывают момент этого
аудита, а не текущий статус. Формальный verdict PARTIAL сохранён.

2026-11-18. **CLEAN_BASELINE_PARTIAL**: доступные локальные проверки пройдены,
отсутствует независимая криптографическая аутентификация depot manifest.
Это новый результат после Steam, а не повторение pre-cleanup проверки.
[Машиночитаемые доказательства](../compatibility/recovery/1287369/post_steam/audit.json).

## Что восстановил Steam

Пользователь выполнил Verify самостоятельно. Диалог о повторном скачивании одного
файла дополнен проверкой `C:\Program Files (x86)\Steam\logs\content_log.txt`:

- 14:27:09 MSK: в `enshrouded.kfc` не совпали 9/9 chunks.
- 14:27:09: Steam удалил лишние 4096 bytes **из конца `enshrouded.kfc_resources`**.
- 14:28:14: full scan 1/61 mismatching files, 51.83 GB.
- 14:28:16: update committed, BuildID26430625, depot1203621,
  manifest7226436020230696061, scheduler result `No Error`.
- Appmanifest: StateFlags4; downloaded4566592/4566592, staged9396224/9396224.

Таким образом, изменились два файла: один скачан заново, второй усечён самим Steam.
Это объясняет отличие inventory от числа файлов в пользовательском диалоге.
Агент не запускал Steam Verify, игру, сервер, writer или моды.

Game: `D:\SteamLibrary\steamapps\common\Enshrouded`.
LOCAL: `C:\Users\user\Saved Games\keen games\Enshrouded`.
Версия1.0.1.2, build1287369, Steam26430625 остались прежними.

| Файл | SHA-256 после Steam | Размер bytes |
|---|---|---:|
| enshrouded.exe | `5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77` | 35476040 |
| enshrouded.kfc | `2093a7cc0859ba2f878fc252a65c36b39605d7e1106e091c63809f6dea460bf5` | 9396224 |
| enshrouded.kfc_resources | `2f54eb9e4677f129c4d527aa9b163d89d0aecee70f2b5b728d7bacaa239d91a7` | 215052288 |

KFC совпал по SHA с удержанным `.bak`; это результат Steam repair, а не применения
карантинной копии. `.bak` не возвращался в каталог игры.

## Полный inventory и сохранность

Новая папка evidence: `runtime/stage10_10_1_post_steam/20261118-audit`.
Baseline сравнения — успешный Phase C cleanup `after.json` (137 файлов),
а не прежние168 или249 файлов.

| Категория | Game | LOCAL |
|---|---:|---:|
| ADDED | 0 | 0 |
| REMOVED | 0 | 0 |
| CHANGED | 2: KFC/resources | 0 |
| UNCHANGED | 135 | 23 |

Повторный полный inventory после Inspector:137/137 game и23/23 LOCAL идентичны
по path/SHA256/size/mtime. Game/server отсутствовали при проверках. Все64 DAT
и все20 оставленных residual files неизменны.

Старый backup209/209, карантин Phase B81/81 и карантин Phase C31/31 повторно
проверены; metadata/journal/receipt также сверены. Существующие копии сохранены.
Новый backup **пока не создан**.

## Depot evidence и предел доверия

Прочитан локальный
`C:\Program Files (x86)\Steam\depotcache\1203621_7226436020230696061.manifest`.
Строгий [read-only parser](../companion/steam_manifest_audit.py) проверяет section
framing, protobuf bounds/duplicates, plaintext identity, CRC, относительные пути,
размеры и SHA-1 всех61 файлов. **61/61 совпали**; дополнительно рассчитаны SHA-256.
В manifest входят EXE, KFC/resources,55 DAT000–054 и3 vendor DLL.

Формат сверялся с исходниками
[SteamKit DepotManifest](https://github.com/SteamRE/SteamKit/blob/master/SteamKit2/SteamKit2/Types/DepotManifest.cs)
и [protobuf schema](https://github.com/SteamTracking/Protobufs/blob/master/steam/content_manifest.proto).
Parser не использует аккаунт, ключи, обход авторизации, скачивание или запуск Steam.

Signature section пустой. CRC защищает от случайного повреждения, но не доказывает
происхождение; локальный cache также может быть изменён. Поэтому проверка не
объявляется независимой аутентификацией Valve и `independent_depot_hashes=false`.
Совокупность доказательств сильнее одного сообщения Steam, но не превращает
PARTIAL в CONFIRMED. Полные per-file hashes опубликованы в audit.json; сырые
игровые ресурсы, сохранения и depot binary в Git не включены.

## Resource-level evidence

Новый режим нашего Inspector собран из исходников, с прежними Cargo.lock и
pinned kfc-parser16708594d686b030d909f2d835b199d879ea9ad8. Это инструмент проекта;
никакие скачанные EMF/game DLL или EXE не исполнялись.

- KFC:55 containers, корректные размеры55 DAT;101492 content references с
  допустимыми container indices/offsets;58 resource chunks внутри resources.
- Resource index:91909 уникальных composite IDs, duplicates0.
- Декодированы все12269 TemplateResource, среди них58 с ActiveNpcState.
  `npcId=2939921867`: collisions0.
- Custom GUID `a1c90001-5e4d-4a91-8a1c-000000000001`: lookup count0.
- Исходный hunter `e3736dff-0ad2-47fc-903c-66c1775836e8` найден.
 82 компонента, FNV32 списка типов `5253f478`; canonical resource SHA256
 `58b9d7cb53d61b4d05b4e7eaf63a0b50109e086f322dbc4b8b3205d48a7a024d`.
-64 ранее исследованных исходных ресурса декодированы заново; отличий от
  pre-Steam значений нет. Дополнительно декодирован animation graph
 `402df515-5965-4b01-a17b-17d482a91af4` с найденным типом
 `keen::anim_graph::runtime_graph::AnimationGraphResource2_0`.
- CharacterPreset1602195472:18 визуальных ссылок разрешены в исследованных
  ресурсах; ModelHierarchy87b29df6-6518-43ef-9298-e3f85a6204b9 содержит102 joints.
- Девять typed HashKey32, Male и useNewProportions=false подтверждены заново.
  Значения и ссылки: [source contract](../compatibility/recovery/1287369/post_steam/source-contract.json).

Это проверка структуры, ссылок и выбранных ресурсов. Не выполнялись полная
декомпрессия всего DAT content, game runtime, регистрация нового clone или render.
Нет утверждения, что NPC уже способен корректно выглядеть или действовать в игре.

## Остаточные файлы

Из137 файлов61 относится к текущему depot,76 не входят в него:

- DAT055–063:9 прежних пустых файлов, **не принадлежат этому depot**, не
  упоминаются новым KFC. Происхождение не объявлено доказанным; оставлены как
  UNKNOWN ownership, не удалялись. Новые shadow DAT могут иметь те же имена,
  но должны быть другими private files внутри `emf/content/client`.
- `enshrouded_local.json`: сохранена локальная конфигурация.
-66 исторических логов/diagnostic files:59 `backup/*.log`,3 EMF log/status,
 4 EML logs. Это не код и не новые подтверждения runtime.

Активные mod artifacts:0. Loader DLL, mod code/manifests, прежние23 mod configs,
`.cache` payload, export evidence и root KFC.bak отсутствуют. Никакие оставшиеся
файлы не изменялись; Steam не считается средством удаления всех сторонних файлов.

В shadow validator исправлена предпосылка «все DAT из каталога — base hardlinks».
Теперь `base_dat_count` берётся из проверенного KFC; девять unreferenced originals
остаются защищёнными single-link файлами. Fixture проверяет допустимый private
shadow DAT с таким же именем и отказ при ссылке на original.

## Acceptance и следующий шаг

Все10 локальных evidence checks evaluator имеют PASS с provenance; его итог
**CLEAN_BASELINE_PARTIAL**, failures0, поскольку authenticated independent hashes
не получены. Флаги evaluator не являются разрешением на операции.

Предложение для пользователя: принять эту конкретную базу **с ограничением
доверия к локальному Steam cache** для небольшого verified backup и офлайн-Phase D.
Это не разрешает установку, запуск игры или NPC. Основание для согласования —
раздел12 исходного ТЗ Phase C/D: «При необходимости представить пользователю
обоснованный вариант ограниченного acceptance с явно указанными рисками».

Подготовленный scope backup:27 payload files, **260563026 bytes** (~260.6 MB):
EXE/KFC/resources, `enshrouded_local.json`, все23 LOCAL. Дополнительно metadata
identity/inventory/hash manifest/future targets. DAT bodies не планируются:
integrated writer должен писать только private shadow. Это расчёт по inventory,
а не уже созданный backup; новый backup должен храниться отдельно от mixed copy.
Перед созданием повторно проверить live identity и неизменность источников.

Полный migration package пока не готов: необходимо завершить patch0.5.0,
evidence v8 framing, observer/bootstrap/контекст LOCAL, Bridge validation,
точный install manifest и актуальный rollback dry-run. Подтверждённые source
данные теперь доступны; принятие ограниченного baseline остаётся отдельным gate.
Настоящая установка Phase E требует отдельного согласия после готового плана.

`clean_baseline_confirmed=false`, `limited_acceptance=PROPOSED_NOT_GRANTED`,
`installation_authorized=false`, `installation_executed=false`,
`runtime_status=NOT_EXECUTED`, `RUNTIME_RENDER_CONFIRMED=UNKNOWN`, `spawn_ready=false`.
