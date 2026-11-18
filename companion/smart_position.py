"""Manual repeated searches with append-only history; one global spawn intent."""
import json
import math
from pathlib import Path
import uuid
from .compatibility import file_hash
from .recovery import no_links
from .experimental_spawn import ExperimentalClient,GUID,validate_context
from .experimental_wait import ContinuationClient


class SearchLedger:
    def __init__(self, root, unused):
        self.root=Path(root);self.unused=unused
        self.directory=self.root/'smart-searches'
        no_links(self.directory);self.directory.mkdir(exist_ok=True)

    def guard(self):
        no_links(self.root/'spawn-intent.json')
        if (self.root/'spawn-intent.json').exists() or not self.unused():
            raise ValueError('SPAWN_SPENT_OR_UNKNOWN_NO_SEARCH')

    def entries(self):
        rows=sorted(self.directory.iterdir())
        for i,p in enumerate(rows,1):
            no_links(p)
            if not p.is_dir() or p.name!=f'{i:06d}':raise ValueError('SEARCH_LEDGER_GAP')
        return rows

    def verify_closed(self,path):
        no_links(path/'closed.json')
        if not (path/'closed.json').exists():raise ValueError('PREVIOUS_SEARCH_NOT_SETTLED')
        closed=json.loads((path/'closed.json').read_text())
        actual={}
        for p in path.iterdir():
            no_links(p)
            if not p.is_file():raise ValueError('SEARCH_HISTORY_LAYOUT')
            if p.name!='closed.json':actual[p.name]=file_hash(p)
        if actual!=closed['files']:raise ValueError('SEARCH_HISTORY_CHANGED')

    def reserve(self):
        self.guard();rows=self.entries()
        for p in rows:self.verify_closed(p)
        path=self.directory/f'{len(rows)+1:06d}'
        path.mkdir()  # Exclusive: two clients cannot claim the same next slot.
        return path

    def settle(self,status):
        self.guard();rows=self.entries()
        if not rows:raise ValueError('NO_SEARCH')
        path=rows[-1]
        for p in rows[:-1]:self.verify_closed(p)
        if (path/'closed.json').exists():raise ValueError('SEARCH_ALREADY_SETTLED')
        if (status.get('state') not in ('READY','STOPPED')
                or status.get('pending')!=0 or status.get('recoverable') is not True
                or status.get('attempted') is not False):raise ValueError('QUERIES_OR_ATTEMPT_UNRESOLVED')
        no_links(path/'probe.json');probe=json.loads((path/'probe.json').read_text())
        if status.get('probe')!=probe['nonce'] or status.get('session')!=probe['session']:
            raise ValueError('SEARCH_SESSION_MISMATCH')
        files={}
        for p in path.iterdir():
            no_links(p)
            if not p.is_file():raise ValueError('SEARCH_HISTORY_LAYOUT')
            files[p.name]=file_hash(p)
        from .recovery import write_json_new
        write_json_new(path/'closed.json',dict(files=files,probe=probe['nonce'],state=status['state'],
                                             pending=0,attempted=False))


class SmartPositionClient(ContinuationClient):
    allow_stopped_status=True
    def __init__(self,transport,binding,root,history,unused,**kwargs):
        self.root=Path(root);self.original_history=history;self.unused=unused
        self.confirmed_position=None
        self.plan={'confirmation_mode':'local_key_after_ready'}
        ExperimentalClient.__init__(self,transport,binding,self.root/'smart-control',**kwargs)
        self.intent_file=self.root/'spawn-intent.json'
        self.ledger=SearchLedger(self.root,unused)
        self.check_history()

    def check_history(self):
        self.ledger.guard()
        for path in self.ledger.entries():
            if (path/'closed.json').exists():
                self.ledger.verify_closed(path)
                if path==self.journal:raise ValueError('SEARCH_ALREADY_SETTLED')
        actual={}
        for p in self.root.rglob('*'):
            no_links(p)
            rel=p.relative_to(self.root).as_posix()
            if rel.split('/')[0] in ('smart-control','smart-searches'):continue
            if p.is_file():actual[rel]=file_hash(p)
        if actual!=self.original_history:raise ValueError('ORIGINAL_HISTORY_CHANGED')

    def context(self):return validate_context(self.transport.hello(),self.transport.state(),body_version='0.1.1')

    def status(self):
        self.check_history()
        value=ExperimentalClient.status(self)
        if self.confirmed_position is not None and (value.get('position')!=self.confirmed_position
                or value.get('pending')!=0 or value.get('attempted') is not False):
            raise ValueError('SELECTED_POSITION_CHANGED')
        return value

    def spawn_once(self,**kwargs):
        no_links(self.journal/'ready-window.json')
        window=json.loads((self.journal/'ready-window.json').read_text(encoding='utf-8'))
        at=window.get('position')
        if (not isinstance(at,dict) or set(at)!=set(('x','y','z'))
                or any(type(n) not in (int,float) or not math.isfinite(n) for n in at.values())):
            raise ValueError('SELECTED_POSITION_INVALID')
        self.confirmed_position=at
        try:return super().spawn_once(**kwargs)
        finally:self.confirmed_position=None

    def open_search(self):
        status=self.status()
        if (status.get('state') not in ('NEW','READY','STOPPED')
                or status.get('pending')!=0 or status.get('recoverable') is not True
                or status.get('attempted') is not False):raise ValueError('SEARCH_NOT_RECOVERABLE')
        self.journal=self.ledger.reserve()
        self.record('search-start.json',dict(session=status['session'],prior_probe=status.get('probe'),
            previous_state=status['state'],time=self.clock(),manual_search=True))

    def prepare(self):
        if self.journal.parent!=self.ledger.directory:raise ValueError('EXPLICIT_SEARCH_REQUIRED')
        self.check_history()
        before=self.context();status=self.status()
        if (status.get('state') not in ('NEW','READY','STOPPED')
                or status.get('pending')!=0 or status.get('recoverable') is not True
                or status.get('attempted') is not False):raise ValueError('SEARCH_NOT_RECOVERABLE')
        nonce=uuid.uuid4().hex
        self.record('probe.json',dict(context=before,session=status['session'],nonce=nonce,
                                     prepared_at=self.clock(),guid=GUID))
        return self.request('probe',status['session'],before['player'],nonce=nonce)

    def settle_search(self):
        # Status journal is outside the now immutable individual search folder.
        self.journal=self.root/'smart-control'
        self.ledger.settle(self.status())
