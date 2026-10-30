# Архитектура собственного humanoid template через EML

## Граница компонентов

```text
EML data patch (до загрузки мира)
  -> новый TemplateResource, GUID, npcId, faction=PlayerAlly
  -> штатные human model/skeleton/animation/component references

EMF Lua Body Adapter (только после отдельных доказательств)
  -> read-only discovery -> IdentityGate -> spawn/move/dismiss gates

Python Body client
  -> personality UUID и команды; entityId остаётся временным handle
```

EML создаёт тип тела. Он не является Brain, не управляет NPC в runtime и не выдаёт ownership конкретного экземпляра. EMF остаётся transport/control layer, Python — внешним orchestration layer.

## Экспериментальный пакет

```text
experimental/eml_humanoid/
  mod.json
  README.md
  src/mod.lua
```

Manifest запрашивает только `patch`. `mod.lua` берёт `hunter_assistant` по подтверждённому GUID, deep-copy создаёт `keen::ecs::TemplateResource` `a1c90001-5e4d-4a91-8a1c-000000000001`, задаёт имя, `PlayerAlly` и `npcId=2939921867`, затем применяет правило регистрации из pinned EMF generator. Любой missing source/component или GUID collision останавливает patch.

`companion/eml_humanoid.py` хранит immutable descriptor и выполняет offline validation. Descriptor не входит в старый spawn allow-list.

## Lifecycle и gates

1. `PATCH_ABSENT`: текущая безопасная норма; runtime выключен.
2. `PATCH_FILES_VALIDATED`: только repository checks.
3. `PATCH_LOADED_READ_ONLY`: будущий эксперимент подтвердил presence нового resource; spawn всё ещё запрещён.
4. `TEMPLATE_FINGERPRINTED`: подтверждены GUID, model, animation graph, faction, components, npcId и отсутствие vanilla mutation.
5. `SPAWN_APPROVED`: отдельное разрешение пользователя и проверенный backup.
6. `SPAWN_UNCERTAIN`: любой ambiguous result; повторный spawn запрещён.
7. `INSTANCE_VERIFIED`: только после session-bound instance marker/ownership proof и нескольких стабильных observations.
8. `SAFE_INACTIVE`: friendly и не выполняет опасное autonomous behavior.
9. `ACTIVE`: разрешены лишь отдельно проверенные capabilities.
10. `DISMISSING`: deletion только с актуальным ownership proof; timeout не снимает lock.
11. `ABSENT`: отсутствие подтверждено многократно.
12. `RECOVERY_REQUIRED`: автоматическое удаление и новый spawn запрещены.

Нынешний descriptor не может пройти к пункту 5: нет model/animation fingerprint, creation marker, ownership proof и safe dismiss.

## Identity contract

Проверки разделяются:

- provenance типа: наш fixed template GUID;
- semantic fingerprint: model, animation graph, npcId, faction, component set;
- instance identity: entityId + session + engine instance marker;
- ownership: доказательство, что именно этот экземпляр создал наш adapter;
- mutation/delete authority: отдельный свежий gate перед каждой операцией.

Fixed template GUID не заменяет instance marker. Пока подтверждённого marker нет, patch можно только загрузить/read-only обследовать; spawn остаётся выключенным.

## Safety invariants

- source story template читается, но не изменяется;
- новый resource всегда использует отдельный fixed GUID;
- faction задаётся внутри template до появления entity;
- `ActiveNpcState.npcId` вычисляется из нового GUID;
- no autospawn, runtime commands, save paths или inventory mutations;
- unknown/missing/conflicting resources останавливают patch;
- EML patch-load и первый spawn проходят в разных игровых запусках;
- удаление patch не выполняется при наличии неподтверждённой сохранённой entity без восстановления тестового мира;
- capability остаётся выключенной, пока игровое наблюдение не подтвердило её длительное состояние.

## Карта humanoid-зависимостей

```text
TemplateResource
  ModelResource -> RenderModel -> skeleton/skin/materials
  animation graph components -> locomotion/idle/walk/run/turn/death
  ActiveNpcState -> npcId, roaming, GoToPosition receiver, villager state
  Faction -> target/friend rules
  movement/path components -> navigation and collision
  health/actor/target components -> damage and combat candidates
  ForceSave/ActiveNpcStateSaved -> unique NPC persistence candidate
  InventorySetup/Inventory/Equipment -> initialization and transactions
  visual equipment components -> model slots and animation compatibility
  workshop/bed/job/socializing -> unwanted source lifecycle dependencies
```

Deep copy сохраняет ссылки, но каждый узел требует read-only fingerprint. Follow/combat/inventory нельзя выводить только из наличия компонента.

## План интеграции

После подтверждения patch load создать отдельный experimental EMF observer, который только:

1. ищет новый `TemplateResource` по GUID;
2. экспортирует component types и значения model/animation/faction/ActiveNpcState;
3. сравнивает `npcId` и component fingerprint с descriptor;
4. доказывает отсутствие изменений source GUID;
5. не создаёт entity и не пишет world state.

После отдельного решения об instance marker можно расширить `IndependentHumanoidGate`. Протокол `spawn/follow/stay/dismiss` до этого не меняется.

## План первого игрового эксперимента

### Эксперимент A: только загрузка patch

1. Повторно сверить build 1273043, EML 0.2.0 и EMF 0.3.2.
2. Создать/проверить backup отдельного LOCAL test world.
3. Зафиксировать SHA-256 game data до установки.
4. Установить только подтверждённый EML loader и `aic_eml_humanoid` после отдельного разрешения.
5. Пользователь вручную запускает игру; spawn не выполняется.
6. Проверить loader logs и read-only presence/fingerprint нового template.
7. Закрыть игру; проверить сохранения и hashes/changed files.
8. При любой ошибке остановиться, восстановить data и test world по заранее проверенному плану.

### Эксперимент B: один spawn, только после отдельного разрешения

1. Требовать успешный эксперимент A и полный descriptor fingerprint.
2. Сделать новую проверенную копию тестового LOCAL world.
3. Создать один entity рядом с безопасной контрольной зоной.
4. Немедленно read-only подтвердить faction, npcId, template/model/animation и отсутствие агрессии.
5. Не повторять spawn при неопределённом результате.
6. Не вызывать follow/combat/inventory/dismiss до независимого доказательства каждой операции.
7. Закрыть игру и обследовать persistence; восстановить test world при ошибке.

Практический следующий шаг — **не spawn**, а подготовка и отдельное согласование эксперимента A с проверенным бинарным дистрибутивом EML 0.2.0, backup/restore и read-only template observer.
