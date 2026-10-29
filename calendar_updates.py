"""Small, read-only release checker. Installers are opened in the user's browser.

No calendar content is sent to GitHub. No installer is executed by this module.
"""
from pathlib import Path
from urllib.parse import urlsplit
from contextlib import closing
import datetime, hashlib, json, os, re, shutil, subprocess, tempfile, threading, time, urllib.request, webbrowser

REPOSITORY='BlessedHero/sunny-calendar'
API='https://api.github.com/repos/'+REPOSITORY+'/releases/latest'
ASSET='Sunny-Calendar-Setup.exe'
VERSION=re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')

def version(value):
    match=VERSION.fullmatch(str(value))
    if not match:raise ValueError('Invalid release version')
    return tuple(map(int,match.groups()))

def installer_url(tag):
    tag='v'+'.'.join(map(str,version(tag)))
    return 'https://github.com/'+REPOSITORY+'/releases/download/'+tag+'/'+ASSET

class GitHubRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        # The metadata check must stay on GitHub's API, with TLS validation intact.
        u=urlsplit(newurl)
        if u.scheme!='https' or u.hostname!='api.github.com' or u.port not in (None,443) or u.username or u.password:
            raise ValueError('Unexpected update service redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch_release():
    request=urllib.request.Request(API,headers={'Accept':'application/vnd.github+json','User-Agent':'Sunny-Calendar-update-check','X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.build_opener(GitHubRedirects()).open(request,timeout=10) as response:
        body=response.read(2_000_001)
        if len(body)>2_000_000:raise ValueError('Release response too large')
    release=json.loads(body)
    if release.get('draft') or release.get('prerelease'):raise ValueError('Not a stable release')
    tag=release.get('tag_name','');version(tag)
    assets=[a for a in release.get('assets',[]) if a.get('name')==ASSET and a.get('state')=='uploaded']
    if len(assets)!=1:raise ValueError('Installer is not ready')
    asset=assets[0]
    if asset.get('browser_download_url')!=installer_url(tag) or not 0<asset.get('size',0)<100_000_000:
        raise ValueError('Unexpected installer asset')
    if not re.fullmatch(r'sha256:[a-fA-F0-9]{64}',asset.get('digest') or ''):
        raise ValueError('Installer checksum unavailable')
    return {'version':tag.removeprefix('v'),'size':asset['size'],'sha256':asset['digest'][7:].lower(),'url':installer_url(tag)}

def fetch_latest():return fetch_release()['version']

class DownloadRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        u=urlsplit(newurl)
        if u.scheme!='https' or u.hostname not in {'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'} or u.port not in (None,443) or u.username or u.password:
            raise ValueError('Unexpected installer redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def download_installer(release,destination):
    if release['url']!=installer_url('v'+release['version']):raise ValueError('Unexpected installer URL')
    request=urllib.request.Request(release['url'],headers={'User-Agent':'Sunny-Calendar-update-download'})
    partial=destination.with_suffix('.partial');digest=hashlib.sha256();size=0;started=time.monotonic()
    try:
        with urllib.request.build_opener(DownloadRedirects()).open(request,timeout=15) as response,partial.open('wb') as output:
            while True:
                block=response.read(131072)
                if not block:break
                size+=len(block)
                if size>release['size'] or size>100_000_000 or time.monotonic()-started>180:raise ValueError('Installer download interrupted')
                digest.update(block);output.write(block)
        if size!=release['size'] or digest.hexdigest()!=release['sha256']:raise ValueError('Installer checksum mismatch')
        partial.replace(destination)
    finally:
        if partial.exists():partial.unlink()

def native_process_matches(pid,root):
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle:return False
    try:
        text=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(text))
        return bool(kernel.QueryFullProcessImageNameW(handle,0,text,ctypes.byref(size))) and Path(text.value).resolve()==(Path(root)/'Sunny Calendar Demo.exe').resolve()
    finally:kernel.CloseHandle(handle)

class UpdateManager:
    def __init__(self,root,data,document_lock):
        self.root=Path(root);self.data=Path(data);self.document_lock=document_lock
        self.lock=threading.RLock();self.phase='unknown';self.latest=None;self.checked_at=0;self.error=None
        self.cache=self.data/'update-check.json'
        self.prepared=None
        try:
            saved=json.loads(self.cache.read_text(encoding='utf-8'))
            version(saved['latest']);self.latest=saved['latest'];self.checked_at=float(saved['checkedAt'])
            if not 0<self.checked_at<=time.time()+60:raise ValueError('Invalid check time')
            self.phase='known'
        except (OSError,ValueError,KeyError,TypeError):self.latest=None;self.checked_at=0

    def metadata(self):
        try:
            value=json.loads((self.root/'app-release.json').read_text(encoding='utf-8'))
            version(value['version']);return value
        except (OSError,ValueError,KeyError,TypeError):return {'version':'0.0.0','installerUpdates':False}

    def status(self):
        with self.lock:
            meta=self.metadata();phase=self.phase
            if phase=='known':phase='available' if version(self.latest)>version(meta['version']) else 'current'
            return {'phase':phase,'currentVersion':meta['version'],'latestVersion':self.latest,'checkedAt':self.checked_at,
                    'canOpenInstaller':meta.get('installerUpdates') is True,'error':self.error}

    def check(self,automatic=False):
        with self.lock:
            # One check at startup; reloads in a short period reuse the result.
            if self.phase=='checking' or (automatic and self.latest and time.time()-self.checked_at<900):return self.status()
            self.phase='checking';self.error=None
        try:
            latest=fetch_latest();checked=time.time()
            with self.lock:
                self.latest=latest;self.checked_at=checked;self.phase='known'
                self.data.mkdir(parents=True,exist_ok=True)
                temporary=self.cache.with_suffix('.tmp')
                temporary.write_text(json.dumps({'latest':latest,'checkedAt':checked}),encoding='utf-8')
                temporary.replace(self.cache)
        except Exception:
            with self.lock:self.phase='unavailable';self.error='check-failed'
        return self.status()

    def backup(self):
        """Create an ordinary Restore backup JSON, including pasted pictures."""
        import sqlite3
        with self.document_lock:
            records=[];database=self.data/'calendar.sqlite'
            if database.exists():
                with closing(sqlite3.connect(str(database),timeout=15)) as db:
                    records=[json.loads(row[0]) for row in db.execute('SELECT body FROM documents')]
            stamp=datetime.datetime.now(datetime.timezone.utc)
            backup={'format':'sunny-calendar-backup','version':1,'exportedAt':stamp.isoformat(),'docs':records}
            folder=self.data/'backups';folder.mkdir(parents=True,exist_ok=True)
            path=folder/('before-update-'+stamp.strftime('%Y%m%dT%H%M%S%fZ')+'.json')
            temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(backup,ensure_ascii=False),encoding='utf-8');temporary.replace(path)
        return path.name

    def open_installer(self):
        if self.metadata().get('installerUpdates') is not True:raise ValueError('local-test')
        state=self.check()
        if state['phase']!='available':raise ValueError('no-update')
        # Never accept a URL, file path or command from the browser request.
        target=installer_url('v'+state['latestVersion'])
        backup=self.backup()
        if not webbrowser.open(target,new=2):raise ValueError('browser-unavailable')
        return {**self.status(),'downloadOpened':True,'backupCreated':True}

    def prepare_installer(self):
        if self.metadata().get('installerUpdates') is not True:raise ValueError('local-test')
        release=fetch_release()
        if version(release['version'])<=version(self.metadata()['version']):raise ValueError('no-update')
        folder=self.data/'updates';folder.mkdir(parents=True,exist_ok=True)
        installer=folder/('Sunny-Calendar-Setup-'+release['version']+'.exe')
        if not installer.exists() or installer.stat().st_size!=release['size'] or hashlib.sha256(installer.read_bytes()).hexdigest()!=release['sha256']:
            download_installer(release,installer)
        self.backup()
        with self.lock:
            self.prepared={**release,'installer':str(installer.resolve())}
            self.latest=release['version'];self.phase='known'
        return {**self.status(),'prepared':True,'backupCreated':True}

    def launch_installer(self,pid):
        if self.metadata().get('installerUpdates') is not True or not (self.root/'unins000.exe').is_file():raise ValueError('installed-app-required')
        if not native_process_matches(pid,self.root):raise ValueError('wrong-calendar-window')
        prepared=self.prepared
        if not prepared or version(prepared['version'])<=version(self.metadata()['version']):raise ValueError('prepare-update-first')
        installer=Path(prepared['installer'])
        if installer.stat().st_size!=prepared['size'] or hashlib.sha256(installer.read_bytes()).hexdigest()!=prepared['sha256']:raise ValueError('installer-changed')
        self.backup()
        runner=Path(tempfile.mkdtemp(prefix='Sunny-Calendar-update-'))
        shutil.copytree(self.root/'runtime',runner/'runtime',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copyfile(self.root/'apply_update.py',runner/'apply_update.py')
        plan={**prepared,'root':str(self.root.resolve()),'clientPid':int(pid),'serverPid':os.getpid()}
        (runner/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
        subprocess.Popen([str(runner/'runtime/pythonw.exe'),str(runner/'apply_update.py'),str(runner/'plan.json')],cwd=str(runner),creationflags=0x08000000)
        return {'launching':True}

    def handle_get(self,handler,path):
        if path!='/local-api/updates/status':return False
        handler.reply(self.status());return True

    def handle_post(self,path,payload):
        if path=='/local-api/updates/check':return self.check(payload.get('automatic') is True)
        if path=='/local-api/updates/open':return self.open_installer()
        if path=='/local-api/updates/prepare':return self.prepare_installer()
        if path=='/local-api/updates/launch':return self.launch_installer(payload['clientPid'])
        raise ValueError('Unknown update action')
