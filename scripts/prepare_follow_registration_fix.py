"""Prepare exact three-file fix; preserve all previous plans, latches and journals."""
import copy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companion.integrated_deployment import read_pinned
from companion.compatibility import file_hash
from companion.recovery import no_links
from companion.follow import reviewed_continuation, PRIOR_JOURNAL_SHA


def main():
    old=read_pinned(ROOT/'compatibility/experiments/stage10_13/exact-update-manifest.json',
        '5e18844a7999679f1cd0af12fbf49ce00813c023b0bbc3674c90b40dab09b4c8')
    baseline_sha='ac979a13426a5d311bd37f48e502239db238e322980249b1c8f16a2eb8629534'
    baseline=read_pinned(ROOT/'runtime/stage10_13/session471028/post-close/inventory.json',baseline_sha)
    proof=reviewed_continuation(ROOT)
    journal=ROOT/'runtime/stage10_13/test-session.jsonl'
    if file_hash(journal)!=PRIOR_JOURNAL_SHA:raise ValueError('JOURNAL_CHANGED')
    package=ROOT/'dist/stage10_13_movement_0_2_1';no_links(package);package.mkdir(exist_ok=True)
    plan=copy.deepcopy(old);plan.update(version='0.2.1',baseline_sha256=baseline_sha,entries=[],continuation=proof)
    for name in ('main.lua','mod.json','README.md'):
        path='emf/mods/aic_companion_movement/'+name
        p=package/name;no_links(p)
        p.write_bytes((ROOT/'mods/aic_companion_movement'/name).read_bytes().replace(b'\r\n',b'\n'))
        h=file_hash(p)
        plan['entries'].append(dict(path=path,source=name,sha256=h,bytes=p.stat().st_size,
                                   operation='replace',before_sha256=baseline['game'][path]['sha256']))
        for row in plan['effective_files']:
            if row['path']==path:row['sha256']=h
    plan['preserved_intents'].append(dict(path='runtime/stage10_13/test-session.jsonl',sha256=PRIOR_JOURNAL_SHA))
    public=ROOT/'compatibility/experiments/stage10_13/registration-fix';public.mkdir(parents=True,exist_ok=True)
    payload=(json.dumps(plan,indent=2)+'\n').encode()
    for p in (package/'exact-update-manifest.json',public/'exact-update-manifest.json'):
        no_links(p);p.write_bytes(payload)
    print(file_hash(public/'exact-update-manifest.json'))


if __name__=='__main__':main()
