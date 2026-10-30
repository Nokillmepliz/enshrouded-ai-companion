# Experimental EML humanoid template

Это офлайн-прототип формата EML 0.2.0. Он клонирует `hunter_assistant` в новый `TemplateResource`, задаёт новому ресурсу фиксированный GUID, отдельный `npcId` и исходную faction `PlayerAlly`. Исходный story template не изменяется. Capability `export` создаёт диагностический fingerprint нового и исходного ресурсов; завершение записи всё равно должно отдельно подтверждаться положительным журналом writer.

Прототип **не установлен**, не содержит spawn, runtime-команд, доступа к сохранениям и не входит в пакет `aic_body`. Его структурная проверка:

```powershell
.\.tools\python\python.exe -m unittest tests.test_eml_humanoid -v
```

Даже успешная проверка не доказывает загрузку template игрой. Публичный EMF Lua не может независимо найти template GUID без сущности, поэтому observer честно сообщает `UNAVAILABLE_WITHOUT_ENTITY`. До отдельного теста неизвестны совместная загрузка EML/EMF, точные runtime model/animation graph, зависимости workshop lifecycle, ownership конкретного экземпляра и безопасный dismiss. Descriptor имеет `runtime_enabled = false`; spawn запрещён.
