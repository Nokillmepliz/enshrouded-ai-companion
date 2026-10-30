# Этап 10.3 — исправление model fingerprint

Итог: диагностика исправлена, настоящий model fingerprint пока не найден. Статус повторного эксперимента — **BLOCKED** до отдельного разрешения и уточнения визуальной dependency.

## Изменения

- EML patch поднят до `0.2.0`, evidence — до `aic_eml_humanoid_evidence_v2` / `template_evidence_v2.txt`.
- Source и clone проверяются независимо через подтверждённый путь `keen::ecs::ModelResource` → `value.model`.
- Результат типизирован полями `status`, `component`, `field_path`, `value_type`, `value`, `reason`; `model_match=true` возможен только для двух валидных GUID.
- Отсутствующий компонент даёт `MISSING/component_missing`, отсутствующее mapped поле — `MISSING/field_absent_or_unmapped`, неожиданный Lua type и неверный GUID — `UNSUPPORTED`. Значение `nil` больше не преобразуется в текстовый fingerprint.
- Python evaluator требует статус `CONFIRMED`, тип `GUID`, точный component/field path, UUID-формат обоих значений, их фактическое равенство и `model_match=true`. Старый v1 evidence отклоняется.
- Observer читает v2, повторяет fail-closed проверки и отдаёт compact `inspect`; проверка измеряет готовую строку вместе с префиксом EMF и требует не более 1023 байт.

Формат оставлен line-based, потому что EML `io.export` уже подтверждён для текста, а observer не имеет проверенного JSON decoder. Семантика при этом типизирована и однозначна; это не попытка выдать `MISSING` за `CONFIRMED`.

## Что не менялось

Source template не изменяется. Логика GUID, `npcId`, faction, component clone, source unchanged, registry и writer finalization не ослаблена. Patch ничего не спавнит. Runtime Body Adapter остаётся выключен, `spawn_ready=false` вычисляется безусловно.

## Условия будущей проверки

Повторный load-only запуск имеет смысл только после отдельного разрешения пользователя. Он сможет подтвердить корректность typed evidence и компактного observer, но при ожидаемом `MISSING` всё равно завершится `FAILED`; это честный диагностический результат. Для перехода к успеху нужен подтверждённый внешний model dependency или доказательство, что для данного humanoid корректным fingerprint является другой конкретный resource contract. Ни один такой контракт сейчас не установлен.
