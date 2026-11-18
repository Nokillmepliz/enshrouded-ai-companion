"""Offline package/plans only. Reads current baseline; never installs or backs up."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.compatibility import file_hash
from companion.experimental_spawn import GUID, readiness
from companion.integrated_deployment import read_pinned
from companion.integrated_update import check_plan, verify_updated
from companion.patch_update_transaction import snapshot, validate_backup_plan
from companion.recovery import write_json_new, no_links
from scripts.prepare_phase_d_backup import GAME,SAVES,live


def main():
    live()
    public=ROOT/'compatibility/experiments/stage10_11'
    package=ROOT/'dist/stage10_11_first_spawn_0_1_0'
    work=ROOT/'runtime/stage10_11/preparation'
    for p in (public,package,work):
        no_links(p)
        if p.exists():raise ValueError('NEW_OUTPUT_REQUIRED:'+str(p))
    old=ROOT/'compatibility/updates/1287369/0.5.1'
    result=read_pinned(old/'stage10_10_3/load-only/post-close.json',
        '59b7f0460769014c36462b777a618a0af7b7c0f454b5f920ad619ef5647eb93f')
    if result['verdict']['verdict']!='LOAD_ONLY_SUCCESS':raise ValueError('LOAD_ONLY_REQUIRED')
    baseline=read_pinned(Path(result['private_evidence'])/'inventory-after.json',result['after_inventory_sha256'])
    approved=read_pinned(old/'update-manifest.json','a6ef7bd5714353b8b6a3da7354baff4581de7effb1f9409fab4b5f983ac4bdf4')
    prior_package=Path(approved['local_package'])
    plan=read_pinned(prior_package/'update-plan.json',approved['update_plan_sha256']);check_plan(plan,prior_package)
    receipt=read_pinned(old/'installation/receipt.json','8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053')
    verify_updated(plan,approved['update_plan_sha256'],receipt,GAME)
    print('Closed/build/installed16 PASS; verifying current post-close baseline',flush=True)
    current=dict(game=snapshot(GAME),saves=snapshot(SAVES));live()
    if current!=baseline:raise ValueError('BASELINE_CHANGED')
    dest_prefix='emf/mods/aic_first_spawn/'
    destinations=[dest_prefix+n for n in ['mod.json','main.lua','controller.lua','README.md','binding.lua','attempt.lock']]+['emf/config/aic_first_spawn.ini']
    if any((GAME/n).exists() for n in destinations) or (GAME/dest_prefix).exists():raise ValueError('DESTINATION_CONFLICT')
    package.mkdir(parents=True);public.mkdir(parents=True);work.mkdir(parents=True)
    write_json_new(work/'inventory.json',current)
    key=uuid.uuid4().hex
    binding=dict(guid=GUID,build=1287369,key=key)
    write_json_new(package/'client-binding.json',binding)
    for name in ['mod.json','main.lua','controller.lua','README.md']:
        path=package/'payload'/dest_prefix/name;path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'mods/aic_first_spawn'/name,path)
    private=package/'payload'/dest_prefix
    (private/'binding.lua').write_text('return {guid="'+GUID+'",build=1287369,key="'+key+'"}\n',encoding='utf-8',newline='\n')
    (private/'attempt.lock').write_text('UNUSED:'+key,encoding='utf-8',newline='\n')
    ini=package/'payload/emf/config/aic_first_spawn.ini';ini.parent.mkdir(parents=True,exist_ok=True)
    ini.write_text('[aic_first_spawn]\nenabled=1\n',encoding='utf-8',newline='\n')
    entries=[dict(path=n,source='payload/'+n,sha256=file_hash(package/'payload'/n),bytes=(package/'payload'/n).stat().st_size,before_sha256=None) for n in destinations]
    backup=dict(format='aic_stage10_11_local_backup_plan_v1',baseline_inventory_sha256=result['after_inventory_sha256'],
        files=[dict(group='saves',path=n,sha256=r['sha256'],bytes=r['size']) for n,r in sorted(current['saves'].items())],
        payload_bytes=sum(r['size'] for r in current['saves'].values()),save_restore_authorized=False,created=False)
    backup_dest=ROOT/'runtime/backups/stage10_11-local-before-first-spawn'
    validate_backup_plan(backup,{'saves':SAVES},backup_dest,live=live)
    write_json_new(public/'backup-plan.json',backup)
    manifest=dict(format='aic_stage10_11_additive_install_v1',stage='10.11',created_utc=datetime.now(timezone.utc).isoformat(),
        build=1287369,package=str(package),game=str(GAME),entries=entries,
        baseline_inventory_sha256=result['after_inventory_sha256'],baseline_source=str(Path(result['private_evidence'])/'inventory-after.json'),
        prior_receipt_sha256='8fa2fa02ef0ad12b5c3c00864c0e81f21803fc2851872a708dea4e4d8efd2053',
        backup_plan_sha256=file_hash(public/'backup-plan.json'),backup_destination=str(backup_dest),
        client_binding_sha256=file_hash(package/'client-binding.json'),
        installation_authorized=False,spawn_authorized=False,
        expected_post_install_files=23,unchanged_existing_installed_files=16,
        runtime_mutable_file=dict(path=dest_prefix+'attempt.lock',before='UNUSED:<private-key>',after='SPENT!:<same-private-key>',
            rule='Only this exact one-way transition; persist and never reset automatically'),
        removal_plan='Separate permission, closed game, receipt-attributed seven files only, expected mutable latch preserved as evidence',
        readiness=readiness())
    write_json_new(public/'exact-install-manifest.json',manifest)
    write_json_new(package/'exact-install-manifest.json',manifest)
    live()
    # Stable metadata guard; all full hashes above were freshly read.
    for root,rows in [(GAME,current['game']),(SAVES,current['saves'])]:
        if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}!=set(rows):raise ValueError('FINAL_FILE_SET_CHANGED')
        for n,r in rows.items():
            s=(root/n).stat()
            if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)!=(r['volume'],r['file_id'],r['size'],r['mtime_ns'],r['links']):raise ValueError('FINAL_SOURCE_CHANGED')
    output=dict(package_status='OFFLINE_PACKAGE_PREPARED',current_baseline_verified=True,game_files=len(current['game']),LOCAL_files=len(current['saves']),
        installed_existing_verified=16,new_files=7,backup_files=len(backup['files']),backup_bytes=backup['payload_bytes'],
        backup_created=False,installed=False,manifest_sha256=file_hash(public/'exact-install-manifest.json'),**readiness())
    write_json_new(public/'preparation.json',output)
    print(json.dumps(output,indent=2),flush=True)


if __name__=='__main__':main()
