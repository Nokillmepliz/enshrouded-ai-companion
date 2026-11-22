"""Read-only interpretation of recorded NPC state, not a wake/schedule API."""

STATES = {1: 'Start', 2: 'FindBed', 3: 'Idle', 4: 'DecideTask',
          5: 'FindTarget', 6: 'GoToTarget', 7: 'Roam', 8: 'Sleep',
          9: 'Sitting', 10: 'Interacting', 11: 'Socializing',
          13: 'WaitingCloseToPlayer', 16: 'InsideWater', 17: 'FinishTask'}


def classify(discovery):
    state, decision = discovery.get('ai_state'), discovery.get('decision')
    if discovery.get('result') != 'FOUND_ONE':
        return dict(status='IDENTITY_UNCONFIRMED', wake_supported=False)
    blockers = []
    if state in (1, 2, 8, 16):
        blockers.append(STATES[state])
    if decision == 5:
        blockers.append('WantsToSleep')
    if state in (9, 10, 11):
        blockers.append(STATES[state])
    return dict(status='NATIVE_PAUSE' if blockers else 'NO_SCHEDULE_BLOCK_OBSERVED',
                state=STATES.get(state, 'Unknown'), decision=decision,
                blockers=blockers, wake_supported=False,
                movement_ready=False,  # interaction flags, distance and native checks still required
                daytime='NOT_INFERRED_FROM_AI_STATE')


def analyze(records):
    samples = [r['value'] for r in records if r.get('kind') == 'SAMPLE']
    transitions = []
    previous = None
    for sample in samples:
        d = sample.get('discovery', {})
        current = (d.get('session'), d.get('entity'), d.get('ai_state'), d.get('decision'))
        if current != previous:
            transitions.append(dict(session=current[0], entity=current[1],
                                    classification=classify(d)))
        previous = current
    return dict(samples=len(samples), transitions=transitions,
                controller_orders=max((s.get('orders', 0) for s in samples), default=0),
                verdict='BLOCKED_NO_VERIFIED_PER_NPC_SCHEDULE_OVERRIDE',
                installation_ready=False, runtime_ready=False, spawn_ready=False,
                limits='No live read/write, no claim of wake or day/night independence')
