"""Read-only protocol1 client; no generic console or BodyClient fallback."""
import json
import re
import uuid

from .integrated_evidence import parse


def unique_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs)


class IntegratedClient:
    def __init__(self, transport, expected):
        self.transport, self.expected = transport, expected
        self.session = None

    def context(self):
        hello = self.transport.hello()
        wanted = dict(ok=True, emf='0.6.18', api=46, protocol=1, game_build=1287369, process='client')
        if any(type(hello.get(k)) != type(v) or hello.get(k) != v for k,v in wanted.items()):
            raise ValueError('BRIDGE_VERSION_OR_PROCESS')
        if type(hello.get('pid')) != int or hello['pid'] <= 0:
            raise ValueError('BRIDGE_PID')
        state = self.transport.state()
        if state.get('ok') is not True:
            raise ValueError('BRIDGE_STATE_REFUSED')
        world, char = state.get('world') or {}, state.get('character') or {}
        if any(world.get(k) != v for k,v in dict(status='running',kind='server',slot=1,name='AI Body Test').items()):
            raise ValueError('WORLD_CONTEXT')
        if char != dict(storage='local',slot=1,name='Body Test'):
            raise ValueError('CHARACTER_CONTEXT')
        mods = state.get('mods', [])
        ids = [m['id'] for m in mods]
        if len(ids) != len(set(ids)):
            raise ValueError('DUPLICATE_MOD')
        active = {m['id']:m for m in mods if m.get('status') != 'disabled'}
        if set(active) != {'lua','aic_integrated_observer'}:
            raise ValueError('UNREVIEWED_OR_FAILED_MOD')
        for mid, ver, status in [('lua','1.39.0',('loaded',)),('aic_integrated_observer','0.3.0',('script','loaded'))]:
            if active[mid].get('version') != ver or active[mid].get('status') not in status or active[mid].get('reason'):
                raise ValueError('HOST_OR_OBSERVER_MISMATCH')
        return {'pid': hello['pid'], 'character':char, 'world':{k:world[k] for k in ('status','kind','slot','name')}, 'mods':mods}

    def request(self, command):
        if command not in ('status','inspect','compare'):
            raise ValueError('COMMAND_FORBIDDEN')
        nonce = uuid.uuid4().hex
        result = self.transport.console('aic_integrated_observer.'+command+' '+nonce, timeout_ms=5000, settle_ms=100)
        if result.get('ok') is not True or result.get('status') != 'ran' or result.get('truncated', False):
            raise ValueError('OBSERVER_COMMAND_NOT_COMPLETED')
        replies = [line.split('AIC_OBSERVER_V8 ',1)[1] for line in result.get('output',[]) if 'AIC_OBSERVER_V8 ' in line]
        if len(replies) != 1 or len(replies[0]) > 950:
            raise ValueError('OBSERVER_RESPONSE_COUNT_OR_SIZE')
        value = unique_json(replies[0])
        check = dict(schema=8, command=command, nonce=nonce, ok=True, read_only=True, spawn_ready=False,
                     character='Body Test', context_provenance='WORLD_LOCAL_AND_API_REQUIRE_BRIDGE_STATE',
                     eml_runtime_lookup='UNAVAILABLE_CONTENT_UNLOADED',
                     evidence_operation='SESSION_ONLY' if command=='status' else 'PYTHON_LOCAL_VALIDATION_REQUIRED')
        check.update({k:self.expected[k] for k in ('run_token','plan_id','profile_sha256')})
        if any(type(value.get(k)) != type(v) or value.get(k) != v for k,v in check.items()):
            raise ValueError('STALE_OR_INVALID_OBSERVER_RESPONSE')
        token = value.get('session_token')
        if not isinstance(token,str) or not re.fullmatch('[0-9a-fA-F]+-[0-9]+',token) or type(value.get('session')) != int or value['session'] <= 0:
            raise ValueError('SESSION_IDENTITY_MISSING')
        epoch = (token,value['session'])
        if self.session is not None and epoch != self.session:
            raise ValueError('SESSION_CHANGED')
        self.session = epoch
        return value

    def observe(self, command, *, evidence_text=None):
        if command not in ('status','inspect','compare'):
            raise ValueError('COMMAND_FORBIDDEN')
        before = self.context()
        reply = self.request(command)
        after = self.context()
        end = self.request('status')
        if before != after or reply['session_token'] != end['session_token']:
            raise ValueError('CONTEXT_CHANGED')
        evidence = None
        if command != 'status':
            if evidence_text is None: raise ValueError('BUILD_EVIDENCE_REQUIRED')
            evidence = parse(evidence_text,self.expected)
        return {'ok': True,'command':command,'session':reply,'context':after,
                'evidence':evidence,'scope':'SESSION_AND_BUILD_OBSERVATIONS_ONLY',
                'writer_finalized':'UNKNOWN','runtime_render':'UNKNOWN','spawn_ready':False}
