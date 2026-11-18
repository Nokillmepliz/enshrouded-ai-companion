# Дополнительный карантин — точный список для согласования

Статус обновлён18 ноября: **AUTHORIZED AND EXECUTED**,31/31.
[Отчёт и контрольные суммы карантина](STAGE10_10_1_PHASE_C_CLEANUP.md).
Ниже сохранён согласованный список; исторический proposal JSON не переписывается.

Корень всех относительных путей: `D:\SteamLibrary\steamapps\common\Enshrouded`.

Machine-readable [proposal](../compatibility/recovery/1287369/phase_c/residual-proposal.json);
SHA-256 `6e7f462af6ee5d15f0fed6d4eb9b14b06c25f0603dfdcfca2f8456ca5eda6445`.

Предлагаются два отдельных действия:

1. Перенести30 mod/config/cache/catalog/evidence файлов в новый карантин:12660171 bytes.
2. Отдельно сохранить в новом карантине `enshrouded.kfc.bak`:9396224 bytes. Это изоляция недоверенного альтернативного index, а не признание его mod-owned или восстановление vanilla KFC.

Всего31 файл,22056395 bytes (~21.03MiB). Все31 уже входят в повторно проверенный mixed backup. Старые backup/quarantine сохраняются; содержимое карантина не удаляется. Оригинальный KFC/resources, DAT и LOCAL не входят в scope.

Для каждого перемещения: закрытые процессы, build/inventory preflight, verified existing backup, отдельная новая копия в карантине, SHA/size verification, durable journal, повторная проверка исходника и удаление только его имени. При ошибке остановка. Новый executor должен явно поддерживать этот reviewed scope; старый Phase B manifest/receipt не редактировать и старый rollback не запускать.

Restore policy всех строк: сохранить exact copy и журнал; возврат только после отдельного review пути/build/SHA. Не возвращать старые configs в новую установку автоматически. `.bak` не применять поверх KFC; возврат к исходному имени требует отдельного решения, поскольку влияет на выбор базы loader.

## 30 mod artifacts

| Путь | Bytes | SHA-256 | Происхождение и причина |
|---|---:|---|---|
| `.cache/files.json` | 5908 | `62db744032687bce73e60f6ac935debb741ce22ddfda146ceb3c6019b8579aa7` | Generated cache/reflection смешанной базы |
| `.cache/lua/base.lua` | 96560 | `98847ab86a8d73a18ae2b78c53fb73db0c406e776d426d26e36048cb4142c1d0` | Generated cache/reflection смешанной базы |
| `.cache/lua/types.lua` | 1423389 | `a3a4aae161bc29a64dd4e7ec047cd1fcdf2b48d9b18fbc5ff56cc491c429ba47` | Generated cache/reflection смешанной базы |
| `.cache/types.json` | 11106802 | `f3ad9e701fc647acc84aea12de9b5ac6da010423ab856c5b121be1f45eeb99ad` | Generated cache/reflection смешанной базы |
| `emf/config/aic_body.ini` | 23 | `01c055932897eb2657bfce6ff69e1316a533933660c8b0bad5e34d945990c4d5` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/beastmaster.ini` | 26 | `198e014f99f5989dbcbdca26cb6bdfe836727d70ee96a5822a42ba88ed6fe8a2` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/big_stacks.ini` | 25 | `acad9af07c8160cca0d74a15ad7904ca4a4e6c9f14e5a30cc269d8d0cb3ed085` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/bounty.ini` | 21 | `469e3fb39deeee1277dd8041ad2f934b54900f8aee96778c181cb999fed50e68` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/bulk_craft.ini` | 25 | `99ba38dcec606fb39a6b6210d8a0c059619ae86865ce16bf57f8f185ae0e2adc` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/champion.ini` | 23 | `f08c9e9310f53b6a898ba4514d66fc455e1fa73292ca4cdcc77aec033a3f158c` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/clock.ini` | 20 | `5f7ff8e297c3d1313d2c7cad4bb1300873176f8e460cd4450021eac22c1474e1` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/companion.ini` | 24 | `38a9eb54b959cf325dcad1b6acf7884a20657ddcf896fadc1339ed5e8f262ed2` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/grave.ini` | 20 | `5ffccc93daf5e623ef0b671177b55299780130c416253af746049239d2b1db22` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/handover.ini` | 23 | `ad2391a1b6449048323874460b6271fff99cbdb30430985ab9a026da4adf412f` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/herald.ini` | 21 | `7316178fffd943bdefdcc3b366e31bff831c5eb22c72c62bbe0f6b25d751e0dd` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/kill_counter.ini` | 27 | `539042b4f3e44c9c3334d034c8be5d99f5238f9e1a7097a3f975ad0aa825e6cd` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/life_skills.ini` | 26 | `fd44a6b13e9ed9be26cd96d4f8a926d61f519a06d8bee6398586ed4b71cbb4a7` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/loot_magnet.ini` | 26 | `5f605f9ee343667a2b3ee2be16f91ff9ebebbd4f7fb72a70f9275e7d9f8f3305` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/loot_scale.ini` | 25 | `8dd0541812b50125fb4403146d60806a07789ec53bb0ab68bcb969251b98e6ed` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/lua.ini` | 18 | `31da693c4d88b3a9e300f892026b1d5bfa78f2ae5742ada5881ed5c985e9abc2` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/necromancer.ini` | 26 | `5abf505cf65e13fc76da52ea29f8afba31da20e0d33cc6876242462b31d77067` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/quick_stack.ini` | 26 | `1991e487c6e85fac22299c59b387a0726812e62a16d27fe343d199aebd882f76` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/raids.ini` | 20 | `b0825d16c187dcf8c91402f230481beccc97ffdae7d78d155b0c73d5f5bf71ca` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/sleep.ini` | 20 | `2c9e9c00e32d3d3b8db497aea65d66cfac3dc5355c3f922e2623337913f66e43` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/teleports.ini` | 24 | `e43250c16e94b682c6c32c0c403f9947382175f30ab45e38c2d1b04020c824a8` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/config/villager_jobs.ini` | 28 | `fdef1dae8501b8a914cc3411fbb637429b0f586962fe6f0b826e395027474ed8` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/emf_core.ini` | 37 | `c44b117a1485035def743ddc05703b7a93c25a47dee034f80f0fbc8a4bf8656f` | Старая EMF конфигурация; не наследовать при миграции |
| `emf/installed.txt` | 2016 | `0e95129125418a74b4783a38dc9e6d2f089cfd1db8c4b469daad1605bc223b75` | Старый каталог69 файлов, не receipt |
| `emf/mods/aic_body/body.lua` | 15196 | `24a5db4ada4a5b81e9118b4dada51f19f01b8d87c7168887e8c62ace7e84014f` | Исторический AIC body.lua; точное совпадение с026cd8a |
| `export/aic_eml_humanoid/template_evidence_v4.txt` | 9746 | `daec54ef827e215d799ebdb4579ce845e276fe3d2b0873035fbaf333e8e9e4c3` | Историческое evidencev4, не evidence нового run |

## Отдельное согласование KFC.bak

`enshrouded.kfc.bak` —9396224 bytes; SHA-256 `2093a7cc0859ba2f878fc252a65c36b39605d7e1106e091c63809f6dea460bf5`.

KFC4, build1287369,55 containers. Происхождение не подтверждено; original KFC имеет64 containers при том же version string. Pinned choose_base выбрал бы `.bak`. Нельзя объявить его чистым по имени/версии. Предлагается сохранить его вне search path, а настоящий KFC/resources восстановить штатным Steam Verify. Наличие в mixed backup доказывает сохранность копии, не vanilla provenance.

## 20 остатков оставить

- DAT055–063:9 файлов. Не перемещать по номеру/пустому hash; после Verify проверить весь depot/container set.
- NVIDIA/Valve DLL:3 файла. Ранее Valid signatures; не удалять и не заменять вручную.
- `enshrouded_local.json`:1 файл, пользовательские graphics/sound settings.
- Историческая диагностика:7 файлов (loader/core/EML logs и chain_status). Не исполняются и не служат fresh evidence.

Все файлы вне этого31-file scope, включая EXE, KFC/resources, DAT000–054 и LOCAL23, остаются нетронутыми. Пустые директории рекурсивно не удалять.

Повторный audit после очистки завершён: READY_FOR_MANUAL_STEAM_VERIFY.
Установка EMF/patch/observer и Phase E этим согласием не разрешаются.
