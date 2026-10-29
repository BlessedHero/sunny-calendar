"""Small detached installer handoff. The Windows installer stays interactive."""
from pathlib import Path
import ctypes,datetime,hashlib,json,os,subprocess,sys
from ctypes import wintypes

def wait_for_exit(pid):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x00100000,False,int(pid))
    if handle:
        try:
            if kernel.WaitForSingleObject(handle,120000)!=0:raise RuntimeError('Calendar did not close')
        finally:kernel.CloseHandle(handle)

def run(plan):
    root=Path(plan['root']).resolve();exe=root/'Sunny Calendar Demo.exe';installer=Path(plan['installer']).resolve()
    if installer.parent!=(root/'local-data/updates').resolve():raise ValueError('Unexpected installer location')
    if installer.stat().st_size!=plan['size'] or hashlib.sha256(installer.read_bytes()).hexdigest()!=plan['sha256']:raise ValueError('Installer verification failed')
    version=plan['version'];result='failed'
    try:
        wait_for_exit(plan['clientPid']);wait_for_exit(plan['serverPid'])
        # No silent flags. Windows still presents Install/Cancel to the user.
        completed=subprocess.run([str(installer),'/DIR='+str(root),'/NORESTART','/NORESTARTAPPLICATIONS','/SUNNYUPDATE=1'])
        installed=json.loads((root/'app-release.json').read_text(encoding='utf-8'))['version']
        result='updated' if completed.returncode==0 and installed==version else 'not-finished'
    finally:
        data=root/'local-data';data.mkdir(exist_ok=True)
        (data/'last-update.json').write_text(json.dumps({'version':version,'result':result,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}),encoding='utf-8')
        if exe.exists():subprocess.Popen([str(exe)],cwd=str(root))

if __name__=='__main__':
    run(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
