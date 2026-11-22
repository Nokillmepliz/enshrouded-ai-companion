"""Single durable, bounded test session. No retries after an ambiguous Bridge reply."""
import json
import os
from pathlib import Path
import time
import hashlib
import io
from contextlib import contextmanager

from .movement import MovementClient
from .recovery import no_links
from .integrated_deployment import read_pinned

AUDIT_SHA='0f6e5855bb644f25af96de7e2d4d994e311e423d16e30ca48e6f913c55851e34'
PRIOR_JOURNAL_SHA='9c394226b46a4698058c549a2310ab17b7a892d5c41e5256488e50a01fcc76d4'


def reviewed_continuation(root):
    audit=read_pinned(Path(root)/'compatibility/experiments/stage10_13/post-close-471028.json',AUDIT_SHA)
    if (audit.get('status')!='POST_CLOSE_INTEGRITY_PASS_FOLLOW_NOT_STARTED'
        or audit.get('follow_started') is not False or audit.get('movement_commands_executed')!=0
        or audit.get('follow_latch')!='UNUSED' or audit.get('journal_preserved_sha256')!=PRIOR_JOURNAL_SHA):
        raise ValueError('CONTINUATION_NOT_PROVEN')
    return dict(audit_sha256=AUDIT_SHA,prior_journal_sha256=PRIOR_JOURNAL_SHA,
                reason='COMMAND_NOT_REGISTERED_SESSION_NEVER_STARTED')


@contextmanager
def session_stream(journal, continuation):
    if continuation is None:
        with journal.open('x',encoding='utf-8',newline='\n') as stream:yield stream
        return
    # Lock and validate the old bytes before appending. Never truncate/rename/reset.
    with journal.open('r+b') as raw:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(raw.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(raw.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        prior=raw.read()
        if hashlib.sha256(prior).hexdigest()!=continuation['prior_journal_sha256']:
            raise ValueError('CONTINUATION_JOURNAL_CHANGED_OR_ALREADY_USED')
        if not prior.endswith(b'\n'):raise ValueError('INCOMPLETE_PRIOR_JOURNAL')
        raw.seek(0,os.SEEK_END)
        with io.TextIOWrapper(raw,encoding='utf-8',newline='\n') as stream:yield stream


class FollowClient(MovementClient):
    commands = ('discover', 'f_start', 'f_step', 'f_stop', 'f_status')

    def __init__(self, transport, *, version='0.3.0'):
        if version not in ('0.3.0', '0.3.1','0.3.2'):
            raise ValueError('UNREVIEWED_FOLLOW_VERSION')
        super().__init__(transport, version=version)

    def move_to(self, *args, **kwargs):
        raise ValueError('MANUAL_MOVEMENT_DISABLED')


def summarize(samples):
    states = sorted({s['state'] for s in samples})
    distances = [s['distance'] for s in samples if s.get('distance') is not None]
    return dict(samples=len(samples), states_seen=states,
                minimum_player_distance=min(distances) if distances else None,
                maximum_player_distance=max(distances) if distances else None,
                orders=max((s.get('orders', 0) for s in samples), default=0),
                recoveries=max((s.get('recoveries', 0) for s in samples), default=0),
                arrival_observed=any(s.get('reason')=='ARRIVAL_OBSERVED' for s in samples),
                stopped_reason=samples[-1].get('reason') if samples else None,
                roaming_disabled=False, sustained_follow='REQUIRES_GAME_OBSERVATION',
                scenario_coverage='ONLY_STATES_SEEN; missing scenarios are NOT_TESTED',
                spawn_ready=False)


def run(client, journal, token, *, clock=time.monotonic, sleep=time.sleep, continuation=None):
    """Journal each grant; only an audited no-start permits one locked append."""
    journal=Path(journal)
    no_links(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    samples=[]
    start_requested=False
    cleanup_outcome=None
    failure=None
    with session_stream(journal,continuation) as stream:
        def record(kind, value):
            stream.write(json.dumps(dict(kind=kind, time=clock(), value=value), ensure_ascii=False)+'\n')
            stream.flush()
            os.fsync(stream.fileno())
        if continuation is not None:record('AUDITED_CONTINUATION',continuation)
        record('SESSION_INTENT', dict(duration=180, max_orders=24, max_recoveries=2,
                                     interval=1, automatic_retry=False, token=token))
        begun=clock()
        try:
            # No mutation while no player has loaded. Strict LOCAL/mod/build failures stop.
            while True:
                try:
                    client.context()
                    break
                except ValueError as exc:
                    if str(exc)!='PLAYER_UNKNOWN' or clock()-begun>=30:
                        raise
                    record('WAITING_FOR_PLAYER', {})
                    sleep(1)
            d=client.discover()['discovery']
            if d['result']!='FOUND_ONE' or d.get('active_order'):
                raise ValueError('UNIQUE_IDLE_NPC_REQUIRED')
            record('START_GRANT',dict(session=d['session'], entity=d['entity']))
            start_requested=True
            sample=client._request('f_start',token,d['session'],d['entity'])
            samples.append(sample);record('SAMPLE',sample)
            deadline=clock()+175  # Lua hard limit 180; leave room for clean stop.
            seq=0
            while sample['state']!='STOPPED' and clock()<deadline:
                sleep(1)  # no catch-up burst after slow RPC
                if clock()>=deadline: break
                seq+=1
                record('STEP_GRANT',dict(sequence=seq))
                sample=client._request('f_step',token,seq)
                samples.append(sample);record('SAMPLE',sample)
            if sample['state']!='STOPPED':
                record('STOP_GRANT',{})
                sample=client._request('f_stop',token)
                samples.append(sample);record('SAMPLE',sample)
        except (Exception, KeyboardInterrupt) as exc:
            failure=str(exc)
            record('STOPPED_UNKNOWN_NO_RETRY',dict(error=str(exc),
                   action='NO_MUTATION_RETRY; Lua watchdog; 0.3.2 may read cleanup status'))
            raise
        finally:
            if start_requested and getattr(client,'version',None)=='0.3.2':
                # Read-only confirmation, including after REQUEST_ERROR. Never resend stop/move.
                cleanup_outcome='UNCONFIRMED'
                cleanup_error='OBSERVATION_DEADLINE_OR_LIMIT'
                cleanup_deadline=clock()+8
                for _ in range(16):
                    if clock()>=cleanup_deadline: break
                    sleep(.5)
                    try:
                        observed=client._request('f_status')
                        record('CLEANUP_OBSERVATION',observed)
                        if observed.get('state')=='STOPPED' and observed.get('cleanup')=='DONE':
                            cleanup_outcome='CONFIRMED';break
                    except Exception as exc:
                        cleanup_error=str(exc);break
                if cleanup_outcome!='CONFIRMED':record('CLEANUP_UNCONFIRMED',dict(error=cleanup_error))
            report=summarize(samples)
            if cleanup_outcome is not None:report['schedule_cleanup']=cleanup_outcome
            if failure is not None:report['runner_error']=failure
            record('REPORT',report)
    return report
