"""Post-acceptance baseline/backup capture. No game write or installation code."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.clean_backup import create
from companion.compatibility import file_hash, fingerprint
from companion.recovery import inventory, no_links, steam_identity, write_json_new
from companion.residual_quarantine import capture
from scripts.stage10_10_1_phase_c_review import stopped

GAME = Path(r'D:\SteamLibrary\steamapps\common\Enshrouded')
SAVES = Path(r'C:\Users\user\Saved Games\keen games\Enshrouded')
TARGETS = ['dinput8.dll', 'emf/emf_core.dll', 'emf/emf_content.dll', 'emf/mods/lua/lua.dll',
           'emf/mods/lua/mod.json', 'emf/known_tools.txt', 'emf/emf_core.ini', 'emf/config/lua.ini',
           'mods/aic_eml_humanoid/mod.json', 'mods/aic_eml_humanoid/src/mod.lua', 'mods/aic_eml_humanoid/README.md',
           'emf/mods/aic_integrated_observer/mod.json', 'emf/mods/aic_integrated_observer/main.lua',
           'emf/mods/aic_integrated_observer/binding.lua', 'emf/mods/aic_integrated_observer/README.md',
           'emf/config/aic_integrated_observer.ini']


def live():
    stopped()
    manifest = GAME.parents[1] / 'appmanifest_1203620.acf'
    if steam_identity(manifest) != {'steam_build_id': '26430625', 'depot_manifest': '7226436020230696061'}:
        raise ValueError('STEAM_BUILD_CHANGED')
    raw = manifest.read_text(encoding='utf-8-sig')
    def n(key):
        match = re.search('"' + key + r'"\s+"([0-9]+)"', raw)
        if not match: raise ValueError('STEAM_STATE_MISSING')
        return int(match[1])
    if n('StateFlags') != 4 or n('BytesToDownload') != n('BytesDownloaded') or n('BytesToStage') != n('BytesStaged'):
        raise ValueError('STEAM_NOT_IDLE')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--create-accepted-backup', action='store_true')
    args = ap.parse_args()
    audit_path = ROOT / 'compatibility/recovery/1287369/post_steam/audit.json'
    audit = json.loads(audit_path.read_text()); baseline = audit['inventory']
    if audit['verdict']['status'] != 'CLEAN_BASELINE_PARTIAL' or audit['verdict']['failed']:
        raise ValueError('UNEXPECTED_ACCEPTANCE_BASELINE')
    live()
    now = capture({'game': GAME, 'saves': SAVES})
    if any(now[g] != baseline[g] for g in ('game', 'saves')):
        raise ValueError('ACCEPTED_BASELINE_CHANGED')
    if any(n in now['game'] for n in TARGETS):
        raise ValueError('DESTINATION_ALREADY_EXISTS')
    if not args.create_accepted_backup:
        print('READ_ONLY_PREFLIGHT_PASS'); return
    run = ROOT / 'runtime/stage10_10_1_phase_d/accepted-baseline'
    no_links(run); run.mkdir(parents=True, exist_ok=False)
    histories = [ROOT / 'runtime/backups/stage10-10-1-phase-b-20261118T1035Z',
                 ROOT / 'runtime/quarantine/stage10-10-1-phase-b-20261118T1035Z',
                 ROOT / 'runtime/quarantine/stage10-10-1-phase-c-20261118T1122Z']
    history = {p.relative_to(ROOT).as_posix(): inventory(p) for p in histories}
    write_json_new(run / 'history-before.json', history)
    write_json_new(run / 'preflight.json', now)
    acceptance = {'accepted': True, 'accepted_utc': datetime.now(timezone.utc).isoformat(),
        'baseline_sha256': fingerprint(baseline), 'audit_sha256': file_hash(audit_path),
        'formal_verdict': 'CLEAN_BASELINE_PARTIAL', 'independent_depot_hashes': False,
        'scope': 'USER_APPROVED_LIMITED_BASELINE_BACKUP_AND_OFFLINE_PHASE_D',
        'installation_authorized': False, 'spawn_ready': False}
    write_json_new(run / 'acceptance.json', acceptance)
    backup = ROOT / 'runtime/backups/stage10-10-1-clean-20261118'
    manifest = create(backup, {'game': GAME, 'saves': SAVES}, baseline, acceptance,
                      [{'path': n, 'before_sha256': None, 'original_resource_write': False} for n in TARGETS], live=live)
    if history != {p.relative_to(ROOT).as_posix(): inventory(p) for p in histories}:
        raise ValueError('HISTORICAL_BACKUP_OR_QUARANTINE_CHANGED')
    after = capture({'game': GAME, 'saves': SAVES})
    if any(after[g] != baseline[g] for g in ('game', 'saves')):
        raise ValueError('SOURCE_CHANGED_AFTER_BACKUP')
    live(); write_json_new(run / 'after.json', after)
    summary = {'format': 'aic_clean_backup_result_v1', 'backup_path': str(backup),
        'manifest_sha256': file_hash(backup / 'manifest.json'), 'files': len(manifest['payload']),
        'payload_bytes': manifest['payload_bytes'], 'total_bytes': sum(v['size'] for v in inventory(backup).values()),
        'acceptance': acceptance, 'history_unchanged': True, 'game_unchanged': 137, 'local_unchanged': 23,
        'installation_executed': False, 'spawn_ready': False}
    write_json_new(run / 'result.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__': main()
