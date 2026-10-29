"""Small, read-only release checker. Installers are opened in the user's browser.

No calendar content is sent to GitHub. No installer is executed by this module.
"""
from pathlib import Path
from urllib.parse import urlsplit
from contextlib import closing
import datetime, json, re, threading, time, urllib.request, webbrowser

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

def fetch_latest():
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
    return tag.removeprefix('v')

class UpdateManager:
    def __init__(self,root,data,document_lock):
        self.root=Path(root);self.data=Path(data);self.document_lock=document_lock
        self.lock=threading.RLock();self.phase='unknown';self.latest=None;self.checked_at=0;self.error=None
        self.cache=self.data/'update-check.json'
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

    def handle_get(self,handler,path):
        if path!='/local-api/updates/status':return False
        handler.reply(self.status());return True

    def handle_post(self,path,payload):
        if path=='/local-api/updates/check':return self.check(payload.get('automatic') is True)
        if path=='/local-api/updates/open':return self.open_installer()
        raise ValueError('Unknown update action')
