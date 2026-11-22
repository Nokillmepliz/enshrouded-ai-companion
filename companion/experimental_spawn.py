"""Separate, explicit experimental bridge interface; no automatic retries/cleanup."""
import json
import os
from pathlib import Path
import re
import time
import uuid

from .integrated_client import unique_json
from .recovery import no_links

GUID = 'a1c90001-5e4d-4a91-8a1c-000000000001'
AUTHORIZATION = 'I_APPROVE_ONE_DISPOSABLE_SPAWN'


def readiness():
    return dict(status='READY_FOR_EXPERIMENTAL_SPAWN_APPROVAL',
        experimental_spawn_executed=False, production_spawn_ready=False,
        spawn_ready=False, RUNTIME_RENDER_CONFIRMED='UNKNOWN')


def validate_context(hello, state, *, body_version='0.1.0', movement_profile=False, movement_version='0.1.0'):
    wanted = dict(ok=True, emf='0.6.18', api=46, protocol=1,
                  game_build=1287369, process='client')
    if any(type(hello.get(k)) != type(v) or hello.get(k) != v for k, v in wanted.items()):
        raise ValueError('BUILD_OR_BRIDGE_CONTEXT')
    if type(hello.get('pid')) is not int or hello['pid'] <= 0 or state.get('ok') is not True:
        raise ValueError('PROCESS_OR_STATE')
    character = dict(storage='local', slot=1, name='Body Test')
    world = dict(status='running', kind='server', slot=1, name='AI Body Test')
    if state.get('character') != character or any((state.get('world') or {}).get(k) != v for k, v in world.items()):
        raise ValueError('LOCAL_CONTEXT')
    mods = state.get('mods', [])
    active = [m for m in mods if m.get('status') != 'disabled']
    if len({m['id'] for m in active}) != len(active):
        raise ValueError('DUPLICATE_MOD')
    expected = {'lua': ('1.39.0', ('loaded',)),
        'aic_integrated_observer': ('0.3.0', ('script', 'loaded')),
        'aic_first_spawn': (body_version, ('script', 'loaded'))}
    if movement_profile:
        if movement_version not in ('0.1.0','0.1.1','0.1.2','0.2.0','0.2.1', '0.3.0','0.3.1','0.3.2','0.3.3','0.3.4'):
            raise ValueError('UNREVIEWED_MOVEMENT_VERSION')
        expected['aic_companion_movement'] = (movement_version, ('script', 'loaded'))
    if {m['id'] for m in active} != set(expected):
        raise ValueError('UNREVIEWED_MODS')
    for m in active:
        version, statuses = expected[m['id']]
        if m.get('version') != version or m.get('status') not in statuses or m.get('reason'):
            raise ValueError('MOD_VERSION_OR_FAILURE')
    player = state.get('player') or {}
    if type(player.get('id')) is not int or player['id'] <= 0:
        raise ValueError('PLAYER_UNKNOWN')
    if not (player.get('health') or {}).get('value', 0) > 0:
        raise ValueError('PLAYER_NOT_ALIVE')
    return dict(pid=hello['pid'], character=character, world=world, player=player['id'])


class ExperimentalClient:
    def __init__(self, transport, binding, journal_dir, *, clock=time.time):
        if binding.get('guid') != GUID or binding.get('build') != 1287369:
            raise ValueError('TEMPLATE_OR_BUILD_BINDING')
        if not re.fullmatch('[0-9a-f]{32}', binding.get('key', '')):
            raise ValueError('DEPLOYMENT_KEY')
        self.transport, self.binding, self.clock = transport, binding, clock
        self._spawn_permit = False
        self.journal = Path(journal_dir)
        no_links(self.journal)
        self.journal.mkdir(parents=True, exist_ok=True)
        self.intent_file = self.journal/'spawn-intent.json'

    def record(self, name, value):
        path = self.intent_file if name == 'spawn-intent.json' else self.journal/name
        no_links(path)
        with path.open('x', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
            f.flush()
            os.fsync(f.fileno())

    def context(self):
        return validate_context(self.transport.hello(), self.transport.state())

    def request(self, command, *args, nonce=None):
        if command not in ('status', 'probe', 'spawn', 'observe', 'stop'):
            raise ValueError('COMMAND_FORBIDDEN')
        if command == 'spawn':
            if not self._spawn_permit:
                raise ValueError('SPAWN_REQUIRES_AUTHORIZED_DURABLE_INTENT')
            self._spawn_permit = False
        nonce = nonce or uuid.uuid4().hex
        values = [nonce, self.binding['key'], *map(str, args)]
        if any(not re.fullmatch(r'[A-Za-z0-9_-]+', v) for v in values):
            raise ValueError('UNSAFE_ARGUMENT')
        # Exclusive intent is fsynced before sending, including read-only operations.
        self.record(nonce+'-request.json', dict(command=command, args=list(map(str,args)),
            nonce=nonce, time=self.clock(), automatic_retry=False))
        if command == 'spawn' and not self._spawn_not_before <= self.clock() <= self._spawn_deadline-2:
            raise ValueError('SPAWN_DEADLINE_AFTER_JOURNAL_NO_RETRY')
        reply = self.transport.console('aic_first_spawn.'+command+' '+' '.join(values),
                                       timeout_ms=5000, settle_ms=100)
        self.record(nonce+'-response.json', reply)
        if reply.get('ok') is not True or reply.get('status') != 'ran' or reply.get('truncated', False):
            raise ValueError('COMMAND_OUTCOME_UNKNOWN_DO_NOT_RETRY')
        rows = [line.split('AIC_EXPERIMENT ',1)[1] for line in reply.get('output', []) if 'AIC_EXPERIMENT ' in line]
        if len(rows) != 1 or len(rows[0]) > 930:
            raise ValueError('RESPONSE_COUNT_OR_SIZE')
        value = unique_json(rows[0])
        stopped_status=(command=='status' and getattr(self,'allow_stopped_status',False)
                        and value.get('ok') is False and value.get('state')=='STOPPED')
        if value.get('schema') != 1 or value.get('nonce') != nonce or (value.get('ok') is not True and not stopped_status):
            raise ValueError('CONTROLLER_REFUSED:'+str(value.get('reason')))
        if value.get('production_spawn_ready') is not False or value.get('spawn_ready') is not False:
            raise ValueError('INVALID_READINESS_CLAIM')
        return value

    def status(self):
        before = self.context()
        result = self.request('status')
        if self.context() != before or result.get('player') != before['player']:
            raise ValueError('CONTEXT_CHANGED')
        return result

    def prepare(self):
        if self.intent_file.exists():
            raise ValueError('ATTEMPT_ALREADY_CONSUMED')
        before = self.context()
        status = self.status()
        if status['state'] != 'NEW':
            raise ValueError('NOT_NEW')
        nonce = uuid.uuid4().hex
        self.record('probe.json', dict(context=before, session=status['session'],
            nonce=nonce, prepared_at=self.clock(), guid=GUID))
        return self.request('probe', status['session'], before['player'], nonce=nonce)

    def spawn_once(self, *, authorization, clear_area=False, disposable_risk=False):
        if authorization != AUTHORIZATION or clear_area is not True or disposable_risk is not True:
            raise ValueError('EXPLICIT_AUTHORIZATION_AND_RISK_ACCEPTANCE_REQUIRED')
        # No override/retry: independent of the Lua file and kept across reconnect/reload.
        if self.intent_file.exists():
            raise ValueError('ATTEMPT_ALREADY_CONSUMED')
        no_links(self.journal/'probe.json')
        probe = json.loads((self.journal/'probe.json').read_text(encoding='utf-8'))
        if probe['guid'] != GUID or not 0 <= self.clock()-probe['prepared_at'] <= 20:
            raise ValueError('PROBE_EXPIRED')
        ctx = self.context()
        if ctx != probe['context']:
            raise ValueError('CONTEXT_CHANGED')
        status = self.status()
        if status['state'] != 'READY' or status['session'] != probe['session'] or status['probe'] != probe['nonce']:
            raise ValueError('POSITION_OR_SESSION_UNCONFIRMED')
        # Context/status requests consume time too. Never send at the deadline.
        if not 0 <= self.clock()-probe['prepared_at'] <= 18:
            raise ValueError('PROBE_EXPIRED_OR_SEND_MARGIN')
        self.record('spawn-intent.json', dict(context=ctx, session=probe['session'],
            probe=probe['nonce'], authorization=authorization, manual_area_clear=True,
            disposable_risk_accepted=True, time=self.clock(), outcome='UNKNOWN_UNTIL_OBSERVED'))
        self._spawn_permit = True
        self._spawn_not_before = probe['prepared_at']
        self._spawn_deadline = probe['prepared_at']+20
        result = self.request('spawn', probe['session'], ctx['player'], probe['nonce'], authorization)
        if result.get('session') != probe['session'] or result.get('player') != ctx['player']:
            raise ValueError('SPAWN_RESPONSE_CONTEXT_CHANGED_DO_NOT_RETRY')
        return result

    def observe(self):
        before = self.context()
        result = self.request('observe')
        probe = json.loads((self.journal/'probe.json').read_text(encoding='utf-8'))
        if (self.context() != before or before != probe['context']
                or result.get('session') != probe['session'] or result.get('player') != before['player']):
            raise ValueError('CONTEXT_CHANGED')
        return result
