# Этап 10.4 — проект visual fingerprint

Контракт реализован как изолированный офлайн-модуль [visual_fingerprint.py](../companion/visual_fingerprint.py). Он пока не подключён к Stage 10 evaluator, потому что реальные resource references hunter не получены.

## Контракт

```json
{
  "format": "aic_visual_fingerprint_design_v1",
  "source_template_guid": "...",
  "clone_template_guid": "...",
  "visual_components": ["confirmed component names"],
  "source_resource_references": null,
  "clone_resource_references": null,
  "levels": {
    "STRUCTURAL_MATCH": true,
    "RESOURCE_REFERENCES_MATCH": null,
    "VISUAL_DEPENDENCIES_RESOLVED": null,
    "RUNTIME_RENDER_CONFIRMED": null
  },
  "spawn_ready": false,
  "canonical_sha256": "stable SHA-256"
}
```

`null` означает `UNKNOWN`, а `false` — полученное противоречие. Отсутствующий обязательный component даёт `STRUCTURAL_MATCH=false`. Отсутствующее неэкспортированное runtime field не называется `MISSING`: без чтения соответствующей стадии его состояние неизвестно.

## Уровни

| Уровень | Условие `true` | Текущий результат |
|---|---|---|
| `STRUCTURAL_MATCH` | Source и clone содержат все шесть подтверждённых visual components | `true` по evidence 10.2 |
| `RESOURCE_REFERENCES_MATCH` | Оба отчёта объявляют полный непустой список валидных GUID и списки совпадают | `UNKNOWN` |
| `VISUAL_DEPENDENCIES_RESOLVED` | Списки совпали и каждый GUID найден/декодирован read-only inspector | `UNKNOWN` |
| `RUNTIME_RENDER_CONFIRMED` | Entity реально отрисована и результат наблюдён | всегда `UNKNOWN` на этапе 10.4 |

Ни один более низкий уровень не подменяет следующий. Совпадение пустых списков запрещено. UUID валидируются, сериализация сортирует ключи и использует компактный JSON перед SHA-256. Unknown resource type, неверный GUID, повреждённая структура и неполный список завершаются fail-closed.

## Источники значений

- component set и animation graph: сохранённый EML evidence;
- schema/field types: pinned EMF reflection;
- `CharacterSetup` appearance hashes: будущий EML/KFC read-only report;
- `RenderEquipment.lastModels`: будущий EML report; помечается runtime-derived;
- resource existence/type: будущий проверенный KFC inspector;
- runtime render: только отдельный более поздний игровой тест.

`CharacterSetup` HashKey32 не объявляются resource GUID. `modelHandles`, `renderPoseHandle` и EntityId не являются стабильными межсессионными identifiers и не включаются в resource fingerprint. `lastModels` можно включить только как GUID array с явным происхождением и стадией заполнения.

## Совместимость с evaluator и observer

`companion/stage10.py`, EML patch и observer не изменены на этапе 10.4. Текущий evaluator продолжает требовать подтверждённый model fingerprint v2 и остаётся fail-closed. Подключать новый контракт можно лишь после получения полного непустого списка resource references и проверки существования ресурсов. До этого `LOAD_ONLY_SUCCESS` недостижим по visual-критерию, а `spawn_ready` всегда false.

Будущий evidence должен передавать только компактный результат уровней, count и canonical hash в observer, сохраняя полный JSON во внешнем EML export. Это позволяет остаться в лимите 1023 байта без потери проверяемости: Python сначала проверяет полный файл и hash, observer сообщает hash/status/run token. Формат evidence не повышался, потому что такой runtime export ещё не подтверждён.

## Условия блокировки

- отсутствует любой обязательный visual component;
- source/clone reference lists различаются;
- список пуст, неполон, содержит неверный GUID или неизвестный тип;
- dependency не найдена или не декодируется;
- источник значения не указан;
- попытка считать runtime handle стабильным fingerprint;
- попытка выдать structural match за rendered model;
- нет корреляции run token/source unchanged/writer finalization.

Повторный load-only эксперимент сейчас преждевременен: он может подтвердить чтение новых полей, но без KFC registry/resource resolution не даст `VISUAL_DEPENDENCIES_RESOLVED`. Следующий безопасный шаг — сборка и аудит read-only inspector после отдельного разрешения на локальный Rust toolchain.
