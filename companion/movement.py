"""Explicit discovery/movement prototype. No spawn or implicit retry/cleanup."""
import json
import math
import os
from pathlib import Path
import re
import time
import uuid

from .experimental_spawn import validate_context
from .integrated_client import unique_json
from .recovery import no_links
from .integrated_deployment import read_pinned
from .compatibility import file_hash


def reviewed_20m_attempt(root):
    """One explicit continuation after the audited pre-native refusal; never erase intent."""
    root=Path(root)
    audit=read_pinned(root/'compatibility/experiments/stage10_12/movement-20m/post-close-450416.json',
        'f801a6398ef7e2377f9ed22e4dbfe5f83494811eaec7d3456152504a5b806b78')
    if audit.get('status')!='POST_CLOSE_PASS_MOVE_REFUSED_BEFORE_NATIVE' or audit.get('native_move_called') is not False:
        raise ValueError('PREVIOUS_MOVEMENT_NOT_PROVEN_REFUSED')
    old=root/'runtime/stage10_12/first-movement/movement-intent.json'
    no_links(old)
    if file_hash(old)!=audit['old_movement_intent_sha256']:
        raise ValueError('PREVIOUS_INTENT_CHANGED')
    return root/'runtime/stage10_12/movement-20m-attempt'


class MovementClient:
    commands = ('discover', 'status', 'move_to')
    def __init__(self, transport, *, version='0.1.0'):
        self.transport = transport
        self.version = version
        self.session = None
        self.context_binding = None

    def context(self):
        return validate_context(self.transport.hello(), self.transport.state(),
                                body_version='0.1.1', movement_profile=True, movement_version=self.version)

    def _request(self, command, *args):
        before = self.context()
        if self.context_binding is not None and before != self.context_binding:
            raise ValueError('CONTEXT_CHANGED')
        nonce = uuid.uuid4().hex
        values = [nonce, *map(str, args)]
        if command not in self.commands or any(
                not re.fullmatch(r'[A-Za-z0-9_.-]+', v) for v in values):
            raise ValueError('INVALID_COMMAND')
        response = self.transport.console('aic_companion_movement.'+command+' '+' '.join(values),
                                          timeout_ms=5000, settle_ms=100)
        if response.get('ok') is not True or response.get('status') != 'ran' or response.get('truncated'):
            raise ValueError('OUTCOME_UNKNOWN_NO_RETRY')
        rows = [s.split('AIC_MOVEMENT ', 1)[1] for s in response.get('output', []) if 'AIC_MOVEMENT ' in s]
        if len(rows) != 1 or len(rows[0]) > 950:
            raise ValueError('REPLY_COUNT_OR_SIZE')
        reply = unique_json(rows[0])
        if reply.get('schema') != 1 or reply.get('nonce') != nonce or reply.get('ok') is not True:
            raise ValueError('REFUSED:'+str(reply.get('error')))
        value = reply['value']
        d = value['discovery']
        token = d.get('session')
        if not isinstance(token, str) or not re.fullmatch(r'[0-9a-fA-F]+-[0-9]+', token):
            raise ValueError('SESSION_MISSING')
        if self.session is not None and token != self.session:
            raise ValueError('SESSION_CHANGED')
        if d.get('player') != before['player'] or self.context() != before:
            raise ValueError('CONTEXT_CHANGED')
        self.session, self.context_binding = token, before
        return value

    def discover(self):
        return self._request('discover')

    def status(self):
        return self._request('status')

    def move_to(self, x, y, z, *, approval, intent_path, expected=None):
        if approval != 'APPROVE_PROFILE_ONLY_MOVE':
            raise ValueError('EXPLICIT_APPROVAL_REQUIRED')
        if any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) >= 1000000 for v in (x, y, z)):
            raise ValueError('INVALID_TARGET')
        d = self.discover()['discovery']
        if d.get('result') != 'FOUND_ONE':
            raise ValueError('NO_UNIQUE_CANDIDATE')
        if expected is not None and any(d.get(k)!=expected.get(k) for k in ('session','entity','player')):
            raise ValueError('CONFIRMED_IDENTITY_CHANGED')
        # New movement intent only; NEVER opens/reset the previous spawn intent or latch.
        path = Path(intent_path)
        no_links(path)
        with path.open('x', encoding='utf-8') as f:
            json.dump(dict(session=self.session, entity=d['entity'], target=[x,y,z],
                           approval=approval, time=time.time(), retry=False), f)
            f.flush()
            os.fsync(f.fileno())
        return self._request('move_to', self.session, d['entity'], x, y, z, approval)

    def observe_until_terminal(self, *, seconds=35, clock=time.monotonic, sleep=time.sleep):
        if not 0 < seconds <= 60:
            raise ValueError('OBSERVATION_TIMEOUT')
        deadline = clock()+seconds
        history = []
        while clock() < deadline:
            sample = self.status()
            history.append(sample)
            if sample['state'] != 'ACCEPTED':
                return dict(result=sample['state'], history=history)
            sleep(0.5)
        # Observation timeout is NOT confirmation that an engine order has stopped.
        return dict(result='OBSERVATION_TIMEOUT_NO_RETRY', history=history)


def manual_move(client, intent_path, *, confirm=input, output=print, clock=time.monotonic):
    """One operator-confirmed move to the player's sampled standing position."""
    path=Path(intent_path)
    no_links(path)
    if path.exists():
        raise ValueError('MOVEMENT_INTENT_EXISTS_NO_RETRY')
    d=client.discover()['discovery']
    if d.get('result')!='FOUND_ONE' or d.get('active_order'):
        raise ValueError('NO_UNIQUE_IDLE_CANDIDATE')
    target=d.get('player_position') or {}
    start=d.get('position') or {}
    xyz=[target.get(k) for k in ('x','y','z')]
    origin=[start.get(k) for k in ('x','y','z')]
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in xyz+origin):
        raise ValueError('POSITION_UNAVAILABLE')
    if math.dist(xyz,origin)>20 or abs(xyz[1]-origin[1])>1:
        raise ValueError('STAND_ON_CLEAR_GROUND_WITHIN_20_METRES_OF_NPC')
    output('NPC '+str(d['entity'])+'; target (your standing position): '+str(target))
    output('Confirm daylight, solid clear ground, no water/ledge/obstacle; PROFILE_ONLY identity. One move, no retry.')
    deadline=clock()+30
    if confirm('Type MOVE and Enter to authorize; anything else cancels: ').strip()!='MOVE':
        return dict(result='CANCELLED_NO_MOVE')
    if clock()>=deadline:
        return dict(result='CONFIRMATION_EXPIRED_NO_MOVE')
    path.parent.mkdir(parents=True,exist_ok=True)
    reply=client.move_to(*xyz,approval='APPROVE_PROFILE_ONLY_MOVE',intent_path=path,expected=d)
    output(json.dumps(reply,ensure_ascii=False))
    if reply.get('state')!='ACCEPTED':
        return dict(result=reply.get('state','OUTCOME_UNKNOWN_NO_RETRY'),initial=reply)
    # Separate read-only observation; no cancel even on timeout or exception.
    result=client.observe_until_terminal()
    result['initial']=reply
    return result
