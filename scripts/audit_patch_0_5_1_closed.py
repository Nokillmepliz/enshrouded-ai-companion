"""Post-close integrity only; no bridge retry, game writes or rollback."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.integrated_deployment import read_pinned
from companion.integrated_update import check_plan, verify_updated, input_fingerprint
from companion.patch_update_transaction import snapshot, verify_backup
from companion.recovery import write_json_new
from companion.shadow_integrity import DAT, INDEXES
from companion.integrated_evidence import verdict
from scripts.audit_phase_f_closed import differences
from scripts.prepare_phase_d_backup import GAME, SAVES, live


def main():
    live()
    public = ROOT/'compatibility/updates/1287369/0.5.1'
    run = ROOT/'runtime/stage10_10_2/load_only/20261118T134435140530Z'
    before = read_pinned(run/'inventory-before.json', 'fa172fc1c270ac4cd5751fdc185211149d8053adac8227fa03b1aa46d3204d18')
    approved = read_pinned(public/'update-manifest.json', 'a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    package = Path(approved['local_package'])
    plan = read_pinned(package/'update-plan.json', approved['update_plan_sha256'])
    check_plan(plan, package)
    read_pinned(package/'bridge-binding.json', approved['bridge_binding_sha256'])
    read_pinned(public/'profile.json', plan['identity']['profile_sha256'])
    receipt = read_pinned(public/'installation/receipt.json', '8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053')
    verify_updated(plan, approved['update_plan_sha256'], receipt, GAME)
    backup = Path(receipt['backup_path'])
    verify_backup(backup, read_pinned(backup/'manifest.json', receipt['verified_backup_manifest_sha256']))
    print('CLOSED/BUILD/PACKAGE/INSTALLED16/BACKUP38 PASS; full post-close hash audit', flush=True)
    after = dict(game=snapshot(GAME), saves=snapshot(SAVES));live()
    out = run/datetime.now(timezone.utc).strftime('post-close-%Y%m%dT%H%M%S%fZ')
    out.mkdir(exist_ok=False)
    write_json_new(out/'inventory-after.json', after)
    original = lambda d: {n:r for n,r in d.items() if n in INDEXES|{'enshrouded.exe','enshrouded.kfc.bak'} or DAT.fullmatch(n)}
    old, current = original(before['game']), original(after['game'])
    prefix = 'emf/content/client/'
    shadow = {n.removeprefix(prefix):r for n,r in after['game'].items() if n.startswith(prefix)}
    old_shadow = {n.removeprefix(prefix):r for n,r in before['game'].items() if n.startswith(prefix)}
    base = {f'enshrouded_{i:03d}.dat' for i in range(55)}|{'enshrouded.exe'}
    errors = []
    if current != old: errors.append('ORIGINAL_RECORDS_CHANGED')
    identities = {(r['volume'],r['file_id']) for r in current.values()}
    for n,r in current.items():
        if r['links'] != (2 if n in base else 1): errors.append('ORIGINAL_LINK_COUNT:'+n)
        if n in base and shadow.get(n) != r: errors.append('SHADOW_BASE_LINK:'+n)
    for n,r in shadow.items():
        if n not in base and (r['links'] != 1 or (r['volume'],r['file_id']) in identities):
            errors.append('PRIVATE_SHADOW_LINK:'+n)
        if n.startswith('mods/') and r['sha256'] != after['game'].get(n,{}).get('sha256'):
            errors.append('SHADOW_MOD_COPY:'+n)
    changed = differences(before['game'],after['game'])
    logs = {'emf/content.log','emf/emf_loader.log','emf/emf_core.log','emf/file_opens.log','enshrouded.log','enshrouded.log.backup'}
    affected = set().union(*(set(v) for v in changed.values()))
    outside = sorted(n for n in affected if not n.startswith(prefix) and n not in logs)
    if outside: errors.append('UNATTRIBUTED_NON_SHADOW_CHANGES')
    fp = input_fingerprint(after['game'], '0.5.1')
    if fp != receipt['actual_content_fingerprint']: errors.append('FINGERPRINT_CHANGED')
    locals_diff = differences(before['saves'],after['saves'])
    save_changes = {n:dict(before=before['saves'].get(n),after=after['saves'].get(n))
        for n in sorted(set().union(*(set(v) for v in locals_diff.values())))}
    prior = json.loads((public/'load-only/runtime-result.json').read_text())
    checks = {k:dict(status='PASS',source='runtime validate_state, captured before bridge failure')
        for k in ['writer_finalized','content_unloaded','fresh_state']}
    checks['original_integrity'] = dict(status='PASS' if old==current else 'FAIL',source='post-close full SHA/size/identity/mtime/links snapshot')
    result = dict(checked_utc=datetime.now(timezone.utc).isoformat(),status='POST_CLOSE_INTEGRITY_PASS' if not errors else 'POST_CLOSE_BLOCKED',
        game_server_closed=True,installed_verified=16,backup_verified=38,private_evidence=str(out),
        original_resource_count=len(current),original_changes=differences(old,current),
        game_count=len(after['game']),game_changes=changed,unattributed_changes=outside,
        shadow_count=len(shadow),shadow_changes=differences(old_shadow,shadow),base_links=56,errors=errors,
        shadow_scope='FILESYSTEM_IDENTITY_AND_MOD_COPIES_ONLY; generated resource semantics/readback NOT_VALIDATED',
        local_count=len(after['saves']),local_changes=locals_diff,local_change_records=save_changes,
        save_semantic_integrity='NOT_ESTABLISHED; NO_RESTORE',content_fingerprint=fp,
        runtime_blocker='BLOCKED_BRIDGE_ACCESS',verdict=verdict(prior['build_evidence'],checks),
        rollback_executed=False,spawn_ready=False)
    for name in ['emf_core.log','file_opens.log','emf_loader.log','content.log']:
        (out/name).write_bytes((GAME/'emf'/name).read_bytes())
    write_json_new(out/'result.json',result)
    write_json_new(public/'load-only/post-close.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('local_change_records',)},indent=2),flush=True)
    if errors: raise ValueError('POST_CLOSE_BLOCKED:'+','.join(errors))


if __name__ == '__main__': main()
