# EMF bridge

`emf_bridge.py` copied without functional changes from
[matenm/emf-enshrouded, commit 08d600155fcadc8e45cc9c6f3932a67c717345be](https://github.com/matenm/emf-enshrouded/blob/08d600155fcadc8e45cc9c6f3932a67c717345be/tools/bridge/emf_bridge.py).

Only line endings normalized to LF. SHA-256:
`7c6ca431231dd3628cf2ccf80abe45359e564354afd95c6001628511e88b2b75`.

MIT license: [EMF-LICENSE.txt](EMF-LICENSE.txt). This is the existing Windows named-pipe client, including server process verification and timeouts. It is imported only when a user explicitly invokes a live CLI command. Offline tests use an injected fake bridge; they never discover or connect to the game.
