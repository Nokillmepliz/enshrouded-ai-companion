"""Read-only mirror of pinned EMF content_fingerprint.h and state gates.

The upstream cache fingerprint hashes names/sizes/FILETIMEs, not file contents.
It supplements, and never replaces, our installed/original SHA-256 checks.
"""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from .recovery import no_links


def content_fingerprint(game, *, patch_version='0.5.0'):
    if patch_version not in ('0.5.0', '0.5.1'): raise ValueError('UNSUPPORTED_PATCH_VERSION')
    game=Path(game); no_links(game)
    if (game/'enshrouded.kfc.bak').exists(): raise ValueError('LEGACY_BASE_SELECTION_CONFLICT')
    def fact(label,path,name):
        no_links(path)
        if not path.is_file(): raise ValueError('FINGERPRINT_INPUT_MISSING')
        s=path.stat()
        written=s.st_mtime_ns//100+116444736000000000  # Windows FILETIME epoch
        return f'{label}\t{name}\t{s.st_size}\t{written}\n'
    text='emf content fingerprint 2\nemf\t0.6.18\n'
    for label,name in [('base','enshrouded.kfc'),('kfc','enshrouded.kfc'),
                       ('resources','enshrouded.kfc_resources'),('exe','enshrouded.exe')]:
        text+=fact(label,game/name,name)
    text+=fact('dll',game/'emf/emf_content.dll','emf_content.dll')
    dats=[p for p in game.iterdir() if re.fullmatch(r'enshrouded_[0-9]+\.dat',p.name,re.I) and p.is_file()]
    if len(dats)!=64: raise ValueError('DAT_COUNT_CHANGED')
    text+='dats\t55\t64\n'
    mod=game/'mods/aic_eml_humanoid'
    if {p.name for p in (game/'mods').iterdir()}!={'aic_eml_humanoid'}:
        raise ValueError('UNREVIEWED_CONTENT_MOD')
    for p in mod.rglob('*'): no_links(p)
    files=[p for p in mod.rglob('*') if p.is_file()]
    names={p.relative_to(mod).as_posix() for p in files}
    if names!={'mod.json','README.md','src/mod.lua'}: raise ValueError('CONTENT_MOD_FILE_SET_CHANGED')
    text+=f'mod\taic_eml_humanoid\t{patch_version}\t3\n'
    for p in sorted(files,key=lambda p:p.relative_to(mod).as_posix().lower()):
        text+=fact('file',p,str(p.relative_to(mod)).replace('/','\\'))
    return 'sha256:'+hashlib.sha256(text.encode()).hexdigest()


def validate_state(state, expected_fingerprint, *, not_before, not_after, patch_version='0.5.0'):
    if patch_version not in ('0.5.0', '0.5.1'): raise ValueError('UNSUPPORTED_PATCH_VERSION')
    if not re.fullmatch('sha256:[0-9a-f]{64}',expected_fingerprint): raise ValueError('EXPECTED_FINGERPRINT_REQUIRED')
    if (state.get('fingerprint')!=expected_fingerprint or type(state.get('code'))!=int or state['code']!=0
            or state.get('unloaded') is not True or state.get('truncated') is not False
            or state.get('errors')!=[] or state.get('warnings')!=[]
            or state.get('mods')!=[f'aic_eml_humanoid {patch_version}']):
        raise ValueError('WRITER_NOT_FINALIZED_OR_MISMATCH')
    built=datetime.fromisoformat(state['built_at'].replace('Z','+00:00'))
    if built.tzinfo is None or not not_before <= built <= not_after:
        raise ValueError('STALE_WRITER_STATE')
    return {'status':'PASS','source':'pinned emf_content_state.json + independently recomputed input fingerprint',
            'scope':'WRITER_STATE_ONLY','shadow_readback':'UNKNOWN','resource_redirection':'UNKNOWN','spawn_ready':False}
