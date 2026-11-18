"""Reverify Phase B and prepare an exact proposal. No game writes or cleanup mode."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash, fingerprint, load_profile
from companion.recovery import inventory, no_links, steam_identity, verify_backup, write_json_new
from companion.residual_cleanup import compare_inventory, propose, validate_proposal
from scripts.stage10_10_1_phase_b_audit import kfc_header


def stopped():
    r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
        "$ErrorActionPreference='Stop'; @(Get-Process | Where-Object { $_.ProcessName -in @('enshrouded','enshrouded_server') }).Count"],
        check=True, capture_output=True, text=True, timeout=20)
    if r.stdout.strip() != '0':
        raise ValueError('GAME_OR_SERVER_NOT_CONFIRMED_STOPPED')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--snapshot', type=Path, required=True, help='Fresh full read-only inventory')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    for p in (args.snapshot, args.output):
        no_links(p)
        if not p.resolve().is_relative_to(ROOT):
            raise ValueError('OUTPUT_OR_SNAPSHOT_OUTSIDE_PROJECT')
    stopped()
    base = ROOT / 'compatibility/recovery/1287369'
    plan_path = base / 'cleanup_manifest.json'
    if file_hash(plan_path) != '2d699685c12cb39edc69e924c6a887b4f22dacb218f10ab271713610e3097e4d':
        raise ValueError('PHASE_B_PLAN_CHANGED')
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    plan = read(plan_path)
    operation = read(base / 'phase_b/operation.json')
    backup, quarantine = Path(operation['backup_path']), Path(operation['quarantine_path'])
    if file_hash(backup / 'manifest.json') != operation['backup_manifest_sha256']:
        raise ValueError('BACKUP_MANIFEST_CHANGED')
    verified = verify_backup(plan, backup)
    selected = [e for e in plan['entries'] if e['proposed_action'] == 'QUARANTINE']
    journal = quarantine / 'journal.jsonl'
    if file_hash(journal) != operation['quarantine_journal_sha256']:
        raise ValueError('QUARANTINE_JOURNAL_CHANGED')
    records = [json.loads(line) for line in journal.read_text().splitlines()]
    expected_records = [{'relative_path': e['relative_path'], 'sha256': e['sha256'],
                         'plan_sha256': fingerprint(plan), 'state': state}
                        for e in selected for state in ('COPIED_VERIFIED_SOURCE_PRESENT', 'QUARANTINED')]
    if records != expected_records:
        raise ValueError('QUARANTINE_JOURNAL_MISMATCH')
    expected_files = {e['relative_path']: {'sha256': e['sha256'], 'size': e['size']} for e in selected}
    expected_files['journal.jsonl'] = {'sha256': file_hash(journal), 'size': journal.stat().st_size}
    if inventory(quarantine) != expected_files:
        raise ValueError('QUARANTINE_INTEGRITY_FAILED')
    current = read(args.snapshot)
    age = datetime.now(timezone.utc) - datetime.fromisoformat(current['created_utc'])
    if not 0 <= age.total_seconds() <= 3600:
        raise ValueError('FRESH_SNAPSHOT_REQUIRED')
    previous = read(ROOT / 'runtime/stage10_10_1_phase_b/20261118T1035Z/after.json')
    profile = load_profile(1287369)
    game = Path(plan['roots']['game'])
    identity = {'game_build': profile['game_build'], 'exe_sha256': file_hash(game / 'enshrouded.exe'),
                **steam_identity(Path(plan['steam_manifest_path']))}
    review = read(base / 'phase_b/residual-review.json')
    proposal = propose(review, previous, current, identity, plan['game_identity'])
    validate_proposal(proposal, review, previous, current, identity)
    # Inventory capture and this check are separate observations, not an atomic lock.
    headers = {n: kfc_header(game / n) for n in ('enshrouded.kfc', 'enshrouded.kfc.bak')}
    stopped()
    result = {'format': 'aic_phase_c_pre_steam_review_v1',
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'snapshot_utc': current['created_utc'], 'snapshot_sha256': file_hash(args.snapshot),
              'game_identity': identity, 'delta_from_phase_b': compare_inventory(previous, current),
              'backup_verified_files': len(verified['entries']) + 1,
              'backup_manifest_sha256': file_hash(backup / 'manifest.json'),
              'quarantine_verified_files': len(selected), 'quarantine_journal_sha256': file_hash(journal),
              'headers': headers, 'processes_observed': 0,
              'new_backup_bytes': 0, 'steam_verify': 'NOT_EXECUTED',
              'clean_baseline_confirmed': False, 'phase_c_complete': False,
              'installation_authorized': False, 'installation_executed': False,
              'runtime_status': 'NOT_EXECUTED', 'RUNTIME_RENDER_CONFIRMED': 'UNKNOWN', 'spawn_ready': False}
    args.output.mkdir(parents=True, exist_ok=True)
    write_json_new(args.output / 'pre-steam-review.json', result)
    write_json_new(args.output / 'residual-proposal.json', proposal)
    print(json.dumps({k: result[k] for k in ('game_identity', 'backup_verified_files', 'quarantine_verified_files')}))
    print(json.dumps({a: sum(e['proposed_action'] == a for e in proposal['entries'])
                      for a in sorted({e['proposed_action'] for e in proposal['entries']})}))


if __name__ == '__main__':
    main()
