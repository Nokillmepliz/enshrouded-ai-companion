"""Deadline-based read-only waiting; persistent history and one global spawn intent."""
import json
import math
import time
from pathlib import Path

from .experimental_spawn import ExperimentalClient
from .compatibility import file_hash
from .recovery import no_links


def wait_ready(client, *, interval=0.25, monotonic=time.monotonic, sleep=time.sleep):
    if not 0.25 <= interval <= 0.5:
        raise ValueError('POLL_INTERVAL')
    if (client.journal/'wait-stopped.json').exists():
        raise ValueError('WAIT_ALREADY_STOPPED_NO_RETRY')
    no_links(client.journal/'probe.json')
    probe=json.loads((client.journal/'probe.json').read_text(encoding='utf-8'))
    start=client.clock(); elapsed=start-probe['prepared_at']
    if not math.isfinite(elapsed) or not 0 <= elapsed < 20:
        raise ValueError('PROBE_EXPIRED')
    mono=monotonic(); deadline=mono+20-elapsed
    def remaining():
        wall=client.clock()-probe['prepared_at']
        # Reject clock discontinuities rather than extending the contract.
        if not math.isfinite(wall) or abs((client.clock()-start)-(monotonic()-mono))>0.5:
            raise ValueError('CLOCK_CHANGED')
        return min(20-wall,deadline-monotonic())
    try:
        while remaining()>0:
            status=client.status()
            left=remaining()
            if left<=0:break
            if (status.get('session')!=probe['session'] or status.get('probe')!=probe['nonce']
                    or status.get('player')!=probe['context']['player']):
                raise ValueError('PROBE_CONTEXT_CHANGED')
            phase=status.get('state')
            if phase=='READY':
                result=dict(status='READY',remaining_seconds=left,
                    confirmation_budget_seconds=max(0,left-2),
                    confirmation_window_sufficient=left>=10,
                    minimum_confirmation_seconds=8,send_reserve_seconds=2,
                    deadline_unix=probe['prepared_at']+20,probe=probe['nonce'],
                    session=probe['session'],position=status.get('position'),spawn_ready=False)
                client.record('ready-window.json',result)
                return result
            if phase not in ('GROUND','PATH'):
                raise ValueError('PROBE_'+str(phase)+':'+str(status.get('reason')))
            sleep(min(interval,max(0,remaining())))
        raise TimeoutError('PROBE_DEADLINE_EXPIRED_NO_RETRY')
    except Exception as exc:
        client.record('wait-stopped.json',dict(error=str(exc),time=client.clock(),retry=False))
        raise


def verify_history(root, expected, attempt):
    root=Path(root);no_links(root)
    if (root/'spawn-intent.json').exists():raise ValueError('ATTEMPT_ALREADY_CONSUMED')
    actual={}
    for p in root.rglob('*'):
        no_links(p)
        rel=p.relative_to(root).as_posix()
        if rel==attempt or rel.startswith(attempt+'/'):continue
        if p.is_file():actual[rel]=file_hash(p)
    if actual!=expected:raise ValueError('PROBE_HISTORY_CHANGED')


class ContinuationClient(ExperimentalClient):
    """One planned new session; retains legacy probe and global durable intent."""
    def __init__(self, transport, binding, root, plan, **kwargs):
        self.root=Path(root);self.plan=plan
        attempt=plan['attempt']
        import re
        if not re.fullmatch('attempts/[0-9a-f]{32}',attempt):raise ValueError('ATTEMPT_PATH')
        verify_history(self.root,plan['history'],attempt)
        super().__init__(transport,binding,self.root/attempt,**kwargs)
        self.intent_file=self.root/'spawn-intent.json'

    def status(self):
        verify_history(self.root,self.plan['history'],self.plan['attempt'])
        value=super().status()
        if value.get('session')==self.plan['previous_session']:
            raise ValueError('NEW_GAME_SESSION_REQUIRED')
        return value

    def prepare(self):
        if (self.journal/'probe.json').exists():raise ValueError('PROBE_ALREADY_RECORDED')
        return super().prepare()

    def spawn_once(self, **kwargs):
        if (self.journal/'wait-stopped.json').exists():raise ValueError('WAIT_ALREADY_STOPPED_NO_RETRY')
        no_links(self.journal/'ready-window.json')
        window=json.loads((self.journal/'ready-window.json').read_text(encoding='utf-8'))
        probe=json.loads((self.journal/'probe.json').read_text(encoding='utf-8'))
        if (not window['confirmation_window_sufficient'] or window['probe']!=probe['nonce']
                or window['session']!=probe['session']):
            raise ValueError('INSUFFICIENT_CONFIRMATION_WINDOW')
        return super().spawn_once(**kwargs)
