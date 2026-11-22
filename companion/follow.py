"""Single durable, bounded test session. No retries after an ambiguous Bridge reply."""
import json
import os
from pathlib import Path
import time

from .movement import MovementClient
from .recovery import no_links


class FollowClient(MovementClient):
    commands = ('discover', 'follow_start', 'follow_step', 'follow_stop', 'follow_status')

    def __init__(self, transport):
        super().__init__(transport, version='0.2.0')

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


def run(client, journal, token, *, clock=time.monotonic, sleep=time.sleep):
    """Journal every grant before transmission. The journal is never resumed or rotated."""
    journal=Path(journal)
    no_links(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    samples=[]
    with journal.open('x', encoding='utf-8', newline='\n') as stream:
        def record(kind, value):
            stream.write(json.dumps(dict(kind=kind, time=clock(), value=value), ensure_ascii=False)+'\n')
            stream.flush()
            os.fsync(stream.fileno())
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
            sample=client._request('follow_start',token,d['session'],d['entity'])
            samples.append(sample);record('SAMPLE',sample)
            deadline=clock()+175  # Lua hard limit 180; leave room for clean stop.
            seq=0
            while sample['state']!='STOPPED' and clock()<deadline:
                sleep(1)  # no catch-up burst after slow RPC
                if clock()>=deadline: break
                seq+=1
                record('STEP_GRANT',dict(sequence=seq))
                sample=client._request('follow_step',token,seq)
                samples.append(sample);record('SAMPLE',sample)
            if sample['state']!='STOPPED':
                record('STOP_GRANT',{})
                sample=client._request('follow_stop',token)
                samples.append(sample);record('SAMPLE',sample)
        except (Exception, KeyboardInterrupt) as exc:
            record('STOPPED_UNKNOWN_NO_RETRY',dict(error=str(exc),
                   action='NO_FURTHER_RPC; Lua heartbeat watchdog and finite order deadlines'))
            raise
        finally:
            record('REPORT',summarize(samples))
    return summarize(samples)
