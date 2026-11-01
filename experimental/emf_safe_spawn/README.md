# Safe Spawn Controller — Phase A scaffold

Этот мод **не предназначен для установки**. Manifest выключен, а команды `spawn_once`, `despawn` и `emergency_stop` всегда возвращают `phase_a_mutation_prohibited`. В исходнике нет вызова API создания, удаления, faction, inventory или сохранений.

Команды `status`, `preflight`, `inspect` возвращают только статическое состояние Phase A. Отдельный namespace — `aic_safe_spawn`; read-only observer Stage 10.7 не изменяется.

Будущая runtime-реализация возможна только после отдельного разрешения Phase B, устранения задокументированных блокеров и повторного ревью. Этот scaffold нельзя считать доказательством runtime-безопасности или разрешением на spawn.
