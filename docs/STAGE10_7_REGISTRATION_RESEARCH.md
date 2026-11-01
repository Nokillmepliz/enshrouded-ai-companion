# Stage 10.7 — регистрация и lookup TemplateResource

## Подтверждённый механизм EML

`game.assets.create_resource(value,type,guid,part)` строит `ResourceId(guid, qualified_type_hash, part)`, затем вызывает `AppState::add_resource`. `add_resource` отклоняет дубликат составного ключа, валидирует/клонирует typed value и помещает dirty `ResourceInfo` в map. Возвращаемый `Resource` извлекается из той же map. После выполнения модов patch writer перебирает cached resources, сериализует dirty values, вызывает `write_resource`, затем `finalize`.

`game.assets.get_resource(guid,type,part)` строит тот же составной ключ и вызывает `get_resource_info`. Следовательно, отдельный read-only lookup clone по GUID/type/part без entity поддерживается EML. Patch 0.4.0 повторно делает такой lookup и проверяет GUID, тип, число компонентов и fingerprint. Фактическое подтверждение нового кода требует Phase C.

## GuidRegistryResource

Ни `create_resource`, ни `add_resource`, ни writer не обращаются к `GuidRegistryResource`. Старый patch искал source GUID в первом произвольном registry и добавлял clone только при совпадении. `source_registered=false` означал лишь отсутствие source в этом конкретном списке, а `registry_added=false` — что условная вставка не выполнялась. Это не доказательство неудачи создания. Patch 0.4.0 удаляет неподтверждённую запись и сообщает `guid_registry_status=NOT_REQUIRED` для механизма EML asset manager.

Состояния разделены: `RESOURCE_CREATED`; `RESOURCE_SERIALIZED` (только после writer); `RESOURCE_LOADABLE` (требует load-only); `GUID_REGISTRY_PRESENT` (не применимо к этому API); `TEMPLATE_LOOKUP_AVAILABLE`; `TEMPLATE_LOOKUP_CONFIRMED`; `ENTITY_SPAWNABLE` (не проверяется).

EMF public Lua API по-прежнему не даёт получить arbitrary TemplateResource без entity; `template_of(entity)` зависит от entity. Это не мешает EML asset-manager lookup, но независимое подтверждение игровым runtime loader и spawnability остаётся неизвестным.

Источники: [assets.rs](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/game/assets.rs), [app_state.rs](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/env/app_state.rs), [writer lifecycle](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/crates/mod-loader-lua/src/lib.rs), [официальное описание EML Resource API](https://github.com/Brabb3l/kfc-parser/blob/16708594d686b030d909f2d835b199d879ea9ad8/docs/src/eml/api/assets/resource.md).
