"""Token/ACL/hello-state diagnostic. Never starts a process or changes security."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from companion.recovery import write_json_new
from companion.runtime_validation import bridge_error


def api():
    k=C.WinDLL('kernel32',use_last_error=True);a=C.WinDLL('advapi32',use_last_error=True)
    definitions=[(k,'OpenProcess',[W.DWORD,W.BOOL,W.DWORD],W.HANDLE),
        (k,'CloseHandle',[W.HANDLE],W.BOOL),(k,'LocalFree',[C.c_void_p],C.c_void_p),
        (a,'OpenProcessToken',[W.HANDLE,W.DWORD,C.POINTER(W.HANDLE)],W.BOOL),
        (a,'GetTokenInformation',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)],W.BOOL),
        (a,'ConvertSidToStringSidW',[C.c_void_p,C.POINTER(W.LPWSTR)],W.BOOL),
        (a,'GetNamedSecurityInfoW',[W.LPWSTR,C.c_int,W.DWORD,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.POINTER(C.c_void_p)],W.DWORD),
        (a,'ConvertSecurityDescriptorToStringSecurityDescriptorW',[C.c_void_p,W.DWORD,W.DWORD,C.POINTER(W.LPWSTR),C.c_void_p],W.BOOL)]
    for dll,name,args,result in definitions:
        f=getattr(dll,name);f.argtypes=args;f.restype=result
    return k,a


def token_info(pid):
    k,a=api();process=k.OpenProcess(0x1000,False,pid)
    if not process:raise C.WinError(C.get_last_error())
    token=W.HANDLE()
    try:
        if not a.OpenProcessToken(process,8,C.byref(token)):raise C.WinError(C.get_last_error())
        result={'pid':pid}
        for cls,key in [(1,'user_sid'),(25,'integrity_sid'),(20,'elevated'),(21,'restricted'),(29,'app_container')]:
            size=W.DWORD();a.GetTokenInformation(token,cls,None,0,C.byref(size))
            buf=C.create_string_buffer(size.value)
            if not a.GetTokenInformation(token,cls,buf,size,C.byref(size)):raise C.WinError(C.get_last_error())
            if cls in (1,25):
                sid=C.cast(buf,C.POINTER(C.c_void_p))[0];text=W.LPWSTR()
                if not a.ConvertSidToStringSidW(sid,C.byref(text)):raise C.WinError(C.get_last_error())
                try:result[key]=text.value
                finally:k.LocalFree(C.cast(text,C.c_void_p))
            else:result[key]=bool(C.cast(buf,C.POINTER(W.DWORD))[0])
        return result
    finally:
        if token:k.CloseHandle(token)
        k.CloseHandle(process)


def pipe_security(pid):
    k,a=api();sd=C.c_void_p();text=W.LPWSTR();info=1|4|16  # owner, DACL, mandatory label; no SACL privilege enable
    code=a.GetNamedSecurityInfoW('\\\\.\\pipe\\emf-bridge-'+str(pid),1,info,None,None,None,None,C.byref(sd))
    if code:return dict(status='UNREADABLE',windows_error=code)
    try:
        if not a.ConvertSecurityDescriptorToStringSecurityDescriptorW(sd,1,info,C.byref(text),None):raise C.WinError(C.get_last_error())
        return dict(status='READ',sddl=text.value)
    finally:
        if text:k.LocalFree(C.cast(text,C.c_void_p))
        if sd:k.LocalFree(sd)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--pid',type=int)
    ap.add_argument('--live-read-only',action='store_true')
    args=ap.parse_args()
    if args.pid is not None and (not args.live_read_only or args.pid<=0):ap.error('Positive PID and explicit live authorization required')
    out=args.output.resolve()
    if not out.is_relative_to(ROOT/'runtime') or out.exists():ap.error('New project runtime output required')
    result=dict(client=token_info(os.getpid()),executable=sys.executable,live_requested=args.live_read_only,spawn_ready=False)
    try:
        if args.pid:
            result['game']=token_info(args.pid)
            result['same_user']=result['client']['user_sid']==result['game']['user_sid']
            result['integrity_sufficient']=int(result['client']['integrity_sid'].split('-')[-1])>=int(result['game']['integrity_sid'].split('-')[-1])
            if not result['same_user'] or not result['integrity_sufficient']:
                raise ValueError('TOKEN_CONTEXT_MISMATCH; no connection attempted')
            result['pipe_security']=pipe_security(args.pid)
            if result['pipe_security']['status']!='READ':raise ValueError('PIPE_SECURITY_UNREADABLE; no protocol request attempted')
            from companion.transport import connect
            transport=connect(pid=args.pid)
            try:result.update(hello=transport.hello(),state=transport.state())
            finally:transport.close()
        result['status']='DIAGNOSTIC_COMPLETE'
    except Exception as exc:
        result.update(status='STOPPED',error=str(exc),classification=bridge_error(exc))
    write_json_new(out,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('client','game','state','pipe_security')},indent=2))
    if result['status']=='STOPPED':return 1
    return 0


if __name__=='__main__':sys.exit(main())
