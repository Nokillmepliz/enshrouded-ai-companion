# Integrated observer 0.3.0

Only `aic_integrated_observer.status`, `.inspect`, `.compare` are registered.
Each takes one fresh 32-hex nonce, supplied by the Python client. No entity
mutation, game resource lookup, file write or command evaluation is exposed.

`binding.lua` is generated with the deployment run/plan/profile identities.
The observer reports actual session and character observations. World storage,
world slot/name and EMF/API/host versions are checked independently using Bridge
hello/state before and after the request. Caller-supplied context is not evidence.

The client implements inspect/compare by validating local content.log v8 frames
and their baseline. Lua cannot invoke EML after the integrated content DLL unloads.
Writer completion, finalized shadow readback and actual redirection are separate
mandatory gates. Rendering and spawning remain unconfirmed.
