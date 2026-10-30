"""One local JSONL journal per invocation; never writes into the game directory."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4


class Journal:
    def __init__(self, directory=None):
        directory = Path(directory) if directory else Path(__file__).resolve().parents[1] / 'runtime' / 'logs'
        directory.mkdir(parents=True, exist_ok=True)
        self.run_id = uuid4().hex
        self.path = directory / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + self.run_id + '.jsonl')
        self.file = self.path.open('x', encoding='utf-8')
        self.started = time.monotonic()
        self.failed = False
        # Establish a writable journal BEFORE connecting to a game.
        try:
            self._write('journal_opened', {'path': str(self.path)})
        except Exception:
            self.file.close()
            raise

    def _write(self, event, data):
        self.file.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                                   'elapsed_ms': round((time.monotonic()-self.started)*1000, 3),
                                   'run_id': self.run_id, 'event': event, 'data': data},
                                  ensure_ascii=False) + '\n')
        self.file.flush()
        os.fsync(self.file.fileno())

    def emit(self, event, data=None):
        if self.failed:
            return
        try:
            self._write(event, data)
        except (OSError, ValueError, TypeError) as exc:
            # A logging failure after submission must not abort verification or replay a command.
            self.failed = True
            print('Journal write failed; command verification continues: ' + str(exc), file=sys.stderr)

    def close(self):
        try:
            self.file.close()
        except OSError as exc:
            print('Journal close failed: ' + str(exc), file=sys.stderr)
