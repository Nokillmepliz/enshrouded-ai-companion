# Stage 10.7 — evidence v4

Формат: `aic_eml_humanoid_evidence_v4`, строки `key=value`, уникальные lower_snake_case keys. Каждый запуск получает новый 32-hex run token; токены и runtime dumps не коммитятся.

Для девяти HashKey32 обязательны source/clone `status`, `type=HashKey32`, decimal uint32 `value` и provenance `SOURCE_EML_REFLECTION`/`CLONE_EML_REFLECTION`. Метод: `EML_MAPPED_STRUCT_VALUE_UINT32`. `UNKNOWN`, `UNSUPPORTED`, `MISSING`, invalid range или пустое provenance не проходят H. Равные неподтверждённые значения не считаются совпадением.

Registration diagnostics содержат `resource_created`, состояние сериализации/загрузки, registry status/basis, lookup availability/confirmation/method, GUID, resource type, component count, fingerprint, status/error/provenance и `entity_spawnable=NOT_TESTED`.

Evaluator имеет независимые gates:

- A: patch/GUID/npcId/faction/source/writer/token;
- H: все девять typed values и source=clone;
- R: create, writer serialization, фактически применимое registry rule, EML lookup и identity;
- V: structure, CharacterSetup, animation, references, dependency closure;
- B: LOCAL load и post-run integrity;
- C: Bridge/observer/token/read-only/no truncation.

Evidence v3 принимается для чтения исторических результатов, но возвращает `V3_COMPATIBILITY_ONLY`; H и R не синтезируются. `resource_created != template_lookup_confirmed != spawn_ready`. При любом результате `spawn_ready=false`.
