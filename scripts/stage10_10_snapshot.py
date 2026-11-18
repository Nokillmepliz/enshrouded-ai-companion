"""Read-only game/save inventory. Output must remain inside project runtime."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'D:\SteamLibrary\steamapps\common\Enshrouded')
SAVES = Path(r'C:\Users\user\Saved Games\keen games\Enshrouded')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def snapshot():
    result = {'created_utc': datetime.now(timezone.utc).isoformat(), 'game': {}, 'saves': {}}
    for label, root in (('game', GAME), ('saves', SAVES)):
        if not root.is_dir():
            raise RuntimeError('inventory_root_missing:' + label)
        for path in sorted(root.rglob('*')):
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise RuntimeError('reparse_point_refused')
            if not path.is_file():
                continue
            before = path.stat()
            sha = digest(path)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError('source_changed_during_read')
            result[label][path.relative_to(root).as_posix()] = {
                'bytes': after.st_size, 'mtime_ns': after.st_mtime_ns, 'sha256': sha}
    return result


if __name__ == '__main__':
    name = sys.argv[1]
    if name not in ('before', 'after'):
        raise SystemExit('expected before or after')
    target = ROOT / 'runtime/stage10_10' / (name + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    data = snapshot()
    with target.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
    print(json.dumps({'snapshot': name, 'game_files': len(data['game']), 'save_files': len(data['saves']),
                      'exe': data['game']['enshrouded.exe']}))
