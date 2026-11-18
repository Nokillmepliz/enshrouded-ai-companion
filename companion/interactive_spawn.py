"""Single-process, local console consent. Never launches games or resets history."""
import math
import os
import sys
import time
from .experimental_spawn import AUTHORIZATION
from .experimental_wait import wait_ready


class WindowsKeyboard:
    def __init__(self):
        if os.name!='nt' or not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError('REAL_WINDOWS_CONSOLE_REQUIRED')
        import ctypes
        from ctypes import wintypes
        import msvcrt
        self.msvcrt=msvcrt
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.user.GetAsyncKeyState.argtypes=[ctypes.c_int]
        self.user.GetAsyncKeyState.restype=ctypes.c_short
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetConsoleMode.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.GetConsoleMode.restype=wintypes.BOOL
        mode=wintypes.DWORD()
        if not kernel.GetConsoleMode(msvcrt.get_osfhandle(sys.stdin.fileno()),ctypes.byref(mode)):
            raise ValueError('CONSOLE_INPUT_REQUIRED')

    def drain(self):
        # Bounded even if a key is held or input is continuously injected.
        for _ in range(256):
            if not self.msvcrt.kbhit():return True
            self.msvcrt.getwch()
        return not self.msvcrt.kbhit()

    def released(self):
        return not any(self.user.GetAsyncKeyState(k)&0x8000 for k in (0x59,0x4e,0x1b))

    def poll(self):
        if not self.msvcrt.kbhit():return None
        key=self.msvcrt.getwch()
        if key in ('\x00','\xe0'):
            # A pending scan-code must never be interpreted as a letter Y.
            if self.msvcrt.kbhit():self.msvcrt.getwch()
            else:raise ValueError('INCOMPLETE_EXTENDED_KEY')
            return None
        return key


def confirm_local(client, window, keyboard, *, monotonic=time.monotonic,
                  sleep=time.sleep, output=print):
    wall=client.clock();mono=monotonic()
    deadline=window['deadline_unix'];remaining=deadline-wall
    if not math.isfinite(remaining) or not window['confirmation_window_sufficient'] or remaining<10:
        return 'INSUFFICIENT_CONFIRMATION_WINDOW'
    end=mono+remaining
    def left():
        now=client.clock();m=monotonic()
        if not math.isfinite(now) or abs((now-wall)-(m-mono))>.5:raise ValueError('CLOCK_CHANGED')
        return min(deadline-now,end-m)
    output('READY: '+str(window['position']))
    output('Отпустите Y/N/ESC. Старый ввод будет отброшен. Ждите приглашения Y.')
    # Flush after READY, wait for release, flush again immediately before arming.
    keyboard.drain()
    def pending():
        early_y=False
        for _ in range(256):
            key=keyboard.poll()
            if key is None:return 'Y' if early_y else 'EMPTY'
            if key in ('n','N','\x1b'):return 'CANCEL'
            if key in ('y','Y'):early_y=True
        return 'BUSY'
    quiet=None
    while left()>2:
        queued=pending()
        if queued=='CANCEL':return 'CANCELLED_BY_USER'
        if queued=='EMPTY' and keyboard.released():
            if quiet is None:quiet=monotonic()
            if monotonic()-quiet>=.2:break
        else:quiet=None
        sleep(.025)
    else:return 'CONFIRMATION_TIMEOUT'
    queued=pending()
    if queued=='CANCEL':return 'CANCELLED_BY_USER'
    if queued!='EMPTY' or not keyboard.released():return 'INPUT_NOT_RELEASED'
    output('Y — один spawn, место осмотрено, риск тестового мира принят. N/ESC — отмена. Без Enter.')
    # Also discard input buffered while the prompt was being printed.
    queued=pending()
    if queued=='CANCEL':return 'CANCELLED_BY_USER'
    if queued!='EMPTY' or not keyboard.released():return 'EARLY_OR_HELD_INPUT'
    if left()<10:return 'INSUFFICIENT_CONFIRMATION_WINDOW'
    last=None
    while left()>2:
        seconds=max(0,math.ceil(left()-2))
        if seconds!=last:output(f'До отмены: {seconds} с');last=seconds
        key=keyboard.poll()
        if key in ('n','N','\x1b'):return 'CANCELLED_BY_USER'
        if key in ('y','Y'):
            if left()<=2:return 'CONFIRMATION_TIMEOUT'
            client.record('local-confirmation.json',dict(key='Y',after_ready=True,
                probe=window['probe'],session=window['session'],time=client.clock(),
                remaining_seconds=left(),clear_area=True,disposable_risk=True))
            if left()<=2:return 'CONFIRMATION_TIMEOUT_AFTER_JOURNAL'
            client._local_key_confirmation=window['probe']
            return 'CONFIRMED'
        sleep(.025)
    return 'CONFIRMATION_TIMEOUT'


def run_interactive(client, keyboard, *, monotonic=time.monotonic,
                    sleep=time.sleep, output=print, waiter=wait_ready):
    if client.plan.get('confirmation_mode')!='local_key_after_ready':raise ValueError('LOCAL_PLAN_REQUIRED')
    # Exclusive claim persists on cancel/failure; restarting cannot re-probe.
    client.record('interactive-started.json',dict(time=client.clock(),retry=False))
    try:
        keyboard.drain()
        output('Не двигайтесь. Проверка Ground/Path; заранее нажимать Y нельзя.')
        client.prepare()
        def cancelled():
            # Discard early Y; N/ESC may cancel even during the probe wait.
            for _ in range(256):
                key=keyboard.poll()
                if key is None:return False
                if key in ('n','N','\x1b'):return True
            return False
        window=waiter(client,monotonic=monotonic,sleep=sleep,cancelled=cancelled)
        decision=confirm_local(client,window,keyboard,monotonic=monotonic,sleep=sleep,output=output)
        if decision!='CONFIRMED':
            result=dict(status=decision,spawn_sent=False,spawn_ready=False)
        else:
            # No subprocess or chat round trip. Existing gates/intent/session checks apply.
            reply=client.spawn_once(authorization=AUTHORIZATION,clear_area=True,disposable_risk=True)
            result=dict(status='SPAWN_REPLY_RECEIVED_UNVERIFIED',reply=reply,spawn_ready=False)
        client.record('interactive-result.json',result)
        return result
    except (Exception,KeyboardInterrupt) as exc:
        client.record('interactive-error.json',dict(error=str(exc) or type(exc).__name__,
            time=client.clock(),retry=False,outcome='CHECK_INTENT_AND_REQUESTS_DO_NOT_RETRY'))
        raise
