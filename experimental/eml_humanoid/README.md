# Experimental EML humanoid template

Это офлайн-прототип формата EML 0.2.0. Он клонирует `hunter_assistant` в новый `TemplateResource`, задаёт новому ресурсу фиксированный GUID, отдельный `npcId` и исходную faction `PlayerAlly`. Исходный story template не изменяется.

Прототип **не установлен**, не содержит spawn, runtime-команд, доступа к сохранениям и не входит в пакет `aic_body`. Его структурная проверка:

```powershell
.\.tools\python\python.exe -m unittest tests.test_eml_humanoid -v
```

Даже успешная проверка не доказывает загрузку template игрой. До отдельного теста неизвестны точные унаследованные model/animation graph, зависимости workshop lifecycle, корректность сохранения, ownership конкретного экземпляра и безопасный dismiss. Поэтому descriptor имеет `runtime_enabled = false`, а устанавливать patch и выполнять spawn нельзя.
