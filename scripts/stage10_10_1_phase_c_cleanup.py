"""Approved residual quarantine; default dry-run. Stops on any mismatch/error."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash, fingerprint
from companion.recovery import (inventory, no_links, steam_identity, target, verify_backup, write_json_new)
from companion.residual_quarantine import (capture, check_live, quarantine, selected, validate_before, verify_after)
from scripts.stage10_10_1_phase_c_review import stopped

PROPOSAL_SHA = '6e7f462af6ee5d15f0fed6d4eb9b14b06c25f0603dfdcfca2f8456ca5eda6445'
PLAN_SHA = '2d699685c12cb39edc69e924c6a887b4f22dacb218f10ab271713610e3097e4d'
BACKUP_SHA = '67a542553c82328bcdd589a1f4067c034bf0315fa8e375dd5a89b341c177333b'
JOURNAL_SHA = '27a3a7b79a590e692c14584d1106a3a4f20112e2f26cad005a32abb1e52237d9'
REVIEWED_COMMIT = 'b608cefe376b7a267a67f8b1cb9fdda579d51d6c'


def read(path):
    no_links(path)
    return json.loads(path.read_text(encoding='utf-8'))


def historical_check(plan, backup, old_quarantine):
    if file_hash(backup / 'manifest.json') != BACKUP_SHA or file_hash(old_quarantine / 'journal.jsonl') != JOURNAL_SHA:
        raise ValueError('HISTORICAL_MANIFEST_OR_JOURNAL_CHANGED')
    verified = verify_backup(plan, backup)
    rows = [e for e in plan['entries'] if e['proposed_action'] == 'QUARANTINE']
    expected = {e['relative_path']: {'sha256': e['sha256'], 'size': e['size']} for e in rows}
    expected['journal.jsonl'] = {'sha256': JOURNAL_SHA, 'size': (old_quarantine / 'journal.jsonl').stat().st_size}
    if inventory(old_quarantine) != expected:
        raise ValueError('HISTORICAL_QUARANTINE_CHANGED')
    # Include all files (even metadata/extras) to prove history is preserved later.
    return {'backup': inventory(backup), 'quarantine': expected,
            'verified_backup_payload_files': len(verified['entries']) + 1,
            'verified_quarantine_payload_files': len(rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--destination', type=Path, required=True)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--authorize-30-mod-artifacts', action='store_true')
    ap.add_argument('--authorize-separate-bak-hold', action='store_true')
    args = ap.parse_args()
    for p, root in ((args.run_dir, ROOT / 'runtime'), (args.destination, ROOT / 'runtime/quarantine')):
        no_links(p)
        if not p.resolve().is_relative_to(root.resolve()) or p.resolve() == root.resolve() or p.exists():
            raise ValueError('NEW_PROJECT_RUNTIME_PATH_REQUIRED')
    if (args.run_dir.resolve().is_relative_to(args.destination.resolve())
            or args.destination.resolve().is_relative_to(args.run_dir.resolve())):
        raise ValueError('RUN_AND_QUARANTINE_OVERLAP')
    if args.execute and not (args.authorize_30_mod_artifacts and args.authorize_separate_bak_hold):
        raise ValueError('BOTH_AUTHORIZATIONS_REQUIRED')
    base = ROOT / 'compatibility/recovery/1287369'
    proposal_path = base / 'phase_c/residual-proposal.json'
    plan_path = base / 'cleanup_manifest.json'
    for p, digest in ((proposal_path, PROPOSAL_SHA), (plan_path, PLAN_SHA)):
        reviewed = subprocess.check_output(['git', 'show', REVIEWED_COMMIT + ':' + p.relative_to(ROOT).as_posix()], cwd=ROOT)
        if file_hash(p) != digest or p.read_bytes() != reviewed:
            raise ValueError('REVIEWED_MANIFEST_CHANGED')
    proposal, plan = read(proposal_path), read(plan_path)
    roots = {k: Path(v) for k, v in plan['roots'].items()}
    if set(roots) != {'game', 'saves'}:
        raise ValueError('ROOT_MISMATCH')
    backup = ROOT / 'runtime/backups/stage10-10-1-phase-b-20261118T1035Z'
    old_quarantine = ROOT / 'runtime/quarantine/stage10-10-1-phase-b-20261118T1035Z'

    def live():
        stopped()
        # Only public manifest fields are read; no account/token output.
        manifest = Path(plan['steam_manifest_path'])
        raw = manifest.read_text(encoding='utf-8-sig')
        def number(key):
            m = re.search('"' + key + r'"\s+"([0-9]+)"', raw)
            if not m:
                raise ValueError('STEAM_STATE_UNAVAILABLE')
            return int(m[1])
        if (number('StateFlags') != 4 or number('BytesToDownload') != number('BytesDownloaded')
                or number('BytesToStage') != number('BytesStaged')):
            raise ValueError('STEAM_UPDATE_OR_VERIFY_NOT_IDLE')
        return {'stopped': True, 'identity': {
            'game_build': plan['game_identity']['game_build'],
            'exe_sha256': file_hash(roots['game'] / 'enshrouded.exe'), **steam_identity(manifest)}}

    check_live(proposal, live)
    history = historical_check(plan, backup, old_quarantine)
    print(json.dumps({'backup_verified': history['verified_backup_payload_files'],
                      'old_quarantine_verified': history['verified_quarantine_payload_files']}), flush=True)
    before = capture(roots)
    rows = validate_before(proposal, roots, before, backup)
    check_live(proposal, live)
    args.run_dir.mkdir(parents=True)
    write_json_new(args.run_dir / 'before.json', before)
    write_json_new(args.run_dir / 'history-before.json', history)
    print(json.dumps({'preflight': 'PASS', 'game_files': len(before['game']), 'local_files': len(before['saves']),
                      'selected_files': len(rows), 'payload_bytes': sum(e['size'] for e in rows)}), flush=True)
    if not args.execute:
        print('DRY_RUN_VALID; cleanup_executed=false')
        return
    count = quarantine(proposal, roots, backup, old_quarantine, args.destination, before,
                       authorize_mods=args.authorize_30_mod_artifacts,
                       authorize_bak=args.authorize_separate_bak_hold, live=live)
    print(json.dumps({'quarantined': count, 'post_audit': 'RUNNING'}), flush=True)
    after = capture(roots)
    write_json_new(args.run_dir / 'after.json', after)
    delta = verify_after(proposal, before, after)
    check_live(proposal, live)
    if historical_check(plan, backup, old_quarantine) != history:
        raise ValueError('HISTORY_CHANGED_DURING_OPERATION')
    journal = args.destination / 'journal.jsonl'
    records = [json.loads(line) for line in journal.read_text().splitlines()]
    expected = [{'relative_path': e['relative_path'], 'sha256': e['sha256'], 'size': e['size'],
                 'state': state, 'proposal_identity': fingerprint(proposal)}
                for state in ('COPIED_VERIFIED_SOURCE_PRESENT', 'QUARANTINED') for e in rows]
    if records != expected:
        raise ValueError('NEW_QUARANTINE_JOURNAL_MISMATCH')
    expected_files = {e['relative_path']: {'sha256': e['sha256'], 'size': e['size']} for e in rows}
    for name in ('journal.jsonl', 'proposal.json', 'authorization.json'):
        p = target(args.destination, name)
        expected_files[name] = {'sha256': file_hash(p), 'size': p.stat().st_size}
    if read(args.destination / 'proposal.json') != proposal or inventory(args.destination) != expected_files:
        raise ValueError('NEW_QUARANTINE_CONTENT_MISMATCH')
    result = {'format': 'aic_phase_c_cleanup_receipt_v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'reviewed_commit': REVIEWED_COMMIT, 'reviewed_proposal_sha256': PROPOSAL_SHA,
              'game_identity': proposal['game_identity'], 'quarantine_path': str(args.destination.resolve()),
              'quarantine_payload_files': count, 'quarantine_payload_bytes': sum(e['size'] for e in rows),
              'quarantine_journal_sha256': file_hash(journal), 'quarantine_journal_records': len(records),
              'before_sha256': file_hash(args.run_dir / 'before.json'),
              'after_sha256': file_hash(args.run_dir / 'after.json'), 'delta': delta,
              'unchanged_game_files': len(after['game']), 'unchanged_local_files': len(after['saves']),
              'kept_residual_files': 20, 'unchanged_dat_files': sum(n.endswith('.dat') for n in after['game']),
              'backup_verified_payload_files': history['verified_backup_payload_files'],
              'previous_quarantine_verified_files': history['verified_quarantine_payload_files'],
              'backup_manifest_sha256': BACKUP_SHA, 'previous_quarantine_journal_sha256': JOURNAL_SHA,
              'existing_backup_and_quarantine_preserved': True,
              'cleanup_executed': True, 'separate_bak_held': True, 'bak_restored_over_kfc': False,
              'steam_verify': 'NOT_EXECUTED', 'ready_for_manual_steam_verify': True,
              'clean_baseline_confirmed': False, 'installation_authorized': False, 'installation_executed': False,
              'runtime_status': 'NOT_EXECUTED', 'RUNTIME_RENDER_CONFIRMED': 'UNKNOWN', 'spawn_ready': False}
    write_json_new(args.destination / 'receipt.json', result)
    write_json_new(args.run_dir / 'operation.json', result)
    print(json.dumps({'status': 'READY_FOR_MANUAL_STEAM_VERIFY', 'quarantined': count,
                      'game_remaining': len(after['game']), 'local_unchanged': len(after['saves'])}), flush=True)


if __name__ == '__main__':
    main()
