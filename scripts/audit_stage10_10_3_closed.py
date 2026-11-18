"""Read-only close audit for the authorized PID 202212 load-only session.

Reuses reviewed validators and immutable prior readback. No transport, game
launch, installation, cleanup, save restoration, or rollback entry points.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import file_hash
from companion.integrated_deployment import read_pinned
from companion.integrated_update import check_plan, verify_updated, input_fingerprint
from companion.integrated_evidence import parse, verdict, RUNTIME_GATES
from companion.patch_update_transaction import snapshot, verify_backup
from companion.recovery import write_json_new
from companion.runtime_validation import reassess_post_close, redirection
from companion.shadow_integrity import audit_shadow, DAT, INDEXES
from scripts.audit_phase_f_closed import differences
from scripts.prepare_phase_d_backup import GAME, SAVES, live

RUN = ROOT/'runtime/stage10_10_3/load_only/20261118T141227374049Z'
PUBLIC = ROOT/'compatibility/updates/1287369/0.5.1'


def main():
    live()
    out = RUN/datetime.now(timezone.utc).strftime('post-close-%Y%m%dT%H%M%S%fZ')
    out.mkdir(exist_ok=False)
    try:
        result = audit(out)
    except Exception as exc:
        write_json_new(out/'blocked.json', dict(status='POST_CLOSE_BLOCKED', error=str(exc),
            checked_utc=datetime.now(timezone.utc).isoformat(), spawn_ready=False,
            rollback_executed=False, game_writes=False))
        raise
    write_json_new(out/'result.json', result)
    write_json_new(PUBLIC/'stage10_10_3/load-only/post-close.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in
        ('local_change_records', 'resource_redirection', 'captured_log_hashes')}, indent=2), flush=True)


def audit(out):
    before = read_pinned(RUN/'inventory-before.json',
        '9bb5ef6895915469d1e35a302b2071f2037348049f4f07e0178c39a3237ae904')
    prior = read_pinned(PUBLIC/'stage10_10_3/result.json',
        '24c962649a56e891d6b9b4bc93ea3e3b89552fc9ae2805095ed9db10c5a71cb9')
    checkpoint = read_pinned(RUN/'runtime-checkpoint.json',
        'e79dfa669cbdcb355935f3089aea0901d8496cdef516bf40b10b4fb70b6b6af4')
    for name, digest in checkpoint['private_evidence_hashes'].items():
        read_pinned(RUN/name, digest)
    observer = json.loads((RUN/'observer-compare.stdout.json').read_text())
    diagnostic = json.loads((RUN/'bridge-diagnostic.json').read_text())
    if (checkpoint['pid'] != 202212 or observer['context']['pid'] != 202212
            or diagnostic['hello']['pid'] != 202212 or not observer['ok']
            or diagnostic['status'] != 'DIAGNOSTIC_COMPLETE'
            or checkpoint['status'] != 'RUNTIME_READ_ONLY_CHECKS_PASS_AWAITING_MANUAL_CLOSE'):
        raise ValueError('LIVE_EVIDENCE_NOT_VERIFIED')
    approved = read_pinned(PUBLIC/'update-manifest.json',
        'a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    package = Path(approved['local_package'])
    plan = read_pinned(package/'update-plan.json', approved['update_plan_sha256'])
    check_plan(plan, package)
    binding = read_pinned(package/'bridge-binding.json', approved['bridge_binding_sha256'])
    read_pinned(PUBLIC/'profile.json', plan['identity']['profile_sha256'])
    receipt = read_pinned(PUBLIC/'installation/receipt.json',
        '8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053')
    verify_updated(plan, approved['update_plan_sha256'], receipt, GAME)
    backup = Path(receipt['backup_path'])
    verify_backup(backup, read_pinned(backup/'manifest.json', receipt['verified_backup_manifest_sha256']))
    print('CLOSED / BUILD / INSTALLED16 / BACKUP38 PASS; hashing game and LOCAL', flush=True)
    after = dict(game=snapshot(GAME), saves=snapshot(SAVES))
    live()
    write_json_new(out/'inventory-after.json', after)
    originals = lambda rows: {n: r for n, r in rows.items()
        if n in INDEXES | {'enshrouded.exe', 'enshrouded.kfc.bak'} or DAT.fullmatch(n)}
    old_originals, new_originals = originals(before['game']), originals(after['game'])
    if len(new_originals) != 67 or new_originals != old_originals:
        raise ValueError('ORIGINAL_RESOURCES_CHANGED')
    prefix = 'emf/content/client/'
    shadow = {n.removeprefix(prefix): r for n, r in after['game'].items() if n.startswith(prefix)}
    old_shadow = {n.removeprefix(prefix): r for n, r in before['game'].items() if n.startswith(prefix)}
    if len(shadow) != 77 or shadow != old_shadow:
        raise ValueError('REUSED_SHADOW_CHANGED')
    if shadow != {n: {k: v for k, v in r.items() if k != 'role'}
                  for n, r in prior['shadow_attribution'].items()}:
        raise ValueError('PRIOR_READBACK_RESOURCE_BINDING_CHANGED')
    ns = lambda s: int(datetime.fromisoformat(s).timestamp()*1e9)
    attribution = reassess_post_close(before['game'], after['game'],
        archive='backup/enshrouded_2026-11-18T17-15-49.log',
        session_start_ns=ns('2026-11-18T14:15:49+00:00'),
        session_end_ns=int(datetime.now(timezone.utc).timestamp()*1e9))
    local_diff = differences(before['saves'], after['saves'])
    if local_diff['added'] or local_diff['removed']:
        raise ValueError('LOCAL_FILE_SET_CHANGED')
    if any(r['links'] != 1 or r['size'] <= 0 for r in after['saves'].values()):
        raise ValueError('LOCAL_FILE_EMPTY_OR_LINKED')
    for relative, name in [('default/character0.ksd', 'Body Test'), ('default/world0.ksd', 'AI Body Test')]:
        if (SAVES/relative).read_bytes().count(name.encode()) != 1:
            raise ValueError('LOCAL_SELECTION_NAME_CHANGED')
    captured = {}
    for name in ['enshrouded.log', 'emf/emf_loader.log', 'emf/emf_core.log',
                 'emf/file_opens.log', 'emf/content.log', 'emf/content/client/emf_content_state.json']:
        raw = (GAME/name).read_bytes()
        destination = out/Path(name).name
        destination.write_bytes(raw)
        captured[name] = file_hash(destination)
        if captured[name] != after['game'][name]['sha256']:
            raise ValueError('CAPTURE_CHANGED:'+name)
    fp = input_fingerprint(after['game'], '0.5.1')
    if fp != receipt['actual_content_fingerprint'] or fp != checkpoint['cache']['fingerprint']:
        raise ValueError('FINGERPRINT_CHANGED')
    state = json.loads((out/'emf_content_state.json').read_text())
    if (state['code'] != 0 or state['unloaded'] is not True or state['errors'] or state['warnings']
            or state['fingerprint'] != fp or state['built_at'] != checkpoint['cache']['built_at']):
        raise ValueError('CACHED_WRITER_STATE_CHANGED')
    if 'the shadow copy is current (1 mod, built 2026-11-18T13:46:15Z): emf_content.dll is not loaded' not in (out/'emf_loader.log').read_text():
        raise ValueError('CACHE_REUSE_NOT_REPORTED')
    evidence = parse((out/'content.log').read_text(), binding)
    if evidence != observer['evidence']:
        raise ValueError('BUILD_EVIDENCE_CHANGED')
    redirects = redirection((out/'file_opens.log').read_text(), str(GAME),
        INDEXES | {f'enshrouded_{i:03d}.dat' for i in range(64)},
        started_local='2026-11-18 17:15:49')
    if redirects['status'] != 'PASS':
        raise ValueError('CURRENT_SESSION_REDIRECTION_INCOMPLETE')
    print('ORIGINAL67 / SHADOW77 exact / attribution v2 / LOCAL file set / redirection66 PASS', flush=True)
    original_base = json.loads((ROOT/'runtime/stage10_10_1_phase_f/20261118T122931689254Z/originals-before.json').read_text())
    expected = {n: dict(role=r['role'], sha256=r['sha256']) for n, r in prior['shadow_attribution'].items()}
    filesystem = audit_shadow(GAME, GAME/prefix, original_base, expected, base_dat_count=55)
    if filesystem['shadow_files'] != shadow or filesystem['original_files'] != new_originals:
        raise ValueError('FILES_CHANGED_DURING_SHADOW_AUDIT')
    # Recheck cheap stat identities and saves after the long read-only hash audit.
    from companion.shadow_integrity import no_reparse
    for root, records in [(GAME, after['game']), (SAVES, after['saves'])]:
        if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} != set(records):
            raise ValueError('FINAL_FILE_SET_CHANGED')
        for n, r in records.items():
            p = root/n; no_reparse(p); s = p.stat()
            if (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink) != (
                    r['volume'], r['file_id'], r['size'], r['mtime_ns'], r['links']):
                raise ValueError('FINAL_FILE_CHANGED:'+n)
    if snapshot(SAVES) != after['saves']:
        raise ValueError('SAVES_CHANGED_DURING_AUDIT')
    verify_updated(plan, approved['update_plan_sha256'], receipt, GAME)
    live()
    source = 'post-close.json: exact inventories, audit_shadow, runtime-checkpoint.json and pinned prior readback'
    checks = {k: dict(status='PASS', source=source) for k in RUNTIME_GATES}
    checks['fresh_state']['source'] = ('Verified cache reuse: unchanged 77 shadow records / state / fingerprint; '
        'current PID202212 observer and fresh redirection. No claim of new writer execution.')
    checks['shadow_readback']['source'] = ('stage10_10_3/result.json SHA24c962649a56e891d6b9b4bc93ea3e3b89552fc9ae2805095ed9db10c5a71cb9; '
        '77 resource records unchanged; independent decoder not repeated.')
    return dict(stage='10.10.3', checked_utc=datetime.now(timezone.utc).isoformat(),
        status='POST_CLOSE_INTEGRITY_PASS', game_server_closed=True, private_evidence=str(out),
        before_inventory_sha256=file_hash(RUN/'inventory-before.json'), after_inventory_sha256=file_hash(out/'inventory-after.json'),
        installed_verified=16, backup_verified=38, original_files_unchanged=67,
        original_changes=differences(old_originals, new_originals),
        game_files=len(after['game']), game_changes=differences(before['game'], after['game']),
        post_close_validator=attribution, unattributed_game_changes=[], shadow_files_unchanged=77,
        shadow_filesystem=filesystem['filesystem_integrity'], base_hardlinks=56,
        prior_semantic_readback_reused=True, independent_decoder_rerun=False,
        cached_writer=dict(code=state['code'], unloaded=state['unloaded'], built_at=state['built_at'], fresh_rebuild=False),
        content_fingerprint=fp, resource_redirection=redirects, captured_log_hashes=captured,
        local_files=len(after['saves']), local_changes=local_diff,
        local_change_records={n: dict(before=before['saves'][n], after=after['saves'][n])
            for n in sorted(set(local_diff['content_changed']) | set(local_diff['metadata_changed']))},
        local_selection_names='PASS', local_read_stable_during_audit=True,
        save_semantic_integrity='NOT_ESTABLISHED; game writes during session recorded; NO_RESTORE',
        runtime_context=observer['context'], runtime_checks='BRIDGE_HELLO_STATE_AND_OBSERVER_COMPARE_STATUS_PASS',
        gate_evidence=checks, verdict=verdict(evidence, checks), rollback_executed=False,
        game_writes=False, spawn_ready=False, RUNTIME_RENDER_CONFIRMED='UNKNOWN')


if __name__ == '__main__':
    main()
