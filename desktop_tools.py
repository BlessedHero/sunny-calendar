"""Local-only desktop links and bounded filename search. Never reads file contents."""
import os,sys,json,time,threading,subprocess,uuid,ntpath,ctypes
from ctypes import wintypes
from pathlib import Path
from urllib.parse import urlsplit

CONFIG_LOCK=threading.Lock()
JOBS={}
JOBS_LOCK=threading.Lock()
WORKERS=threading.BoundedSemaphore(2)
OPEN_TYPES={'.pdf','.xlsx','.xls','.xlsm','.docx','.doc','.pptx','.ppt','.txt','.md','.csv','.png','.jpg','.jpeg','.webp','.gif','.rtf'}
SKIP={'.git','node_modules','$recycle.bin','system volume information','__pycache__','.obsidian'}

def defaults():
    return {'roots':[{'label':'Work files','path':str(Path.home()/'Documents'/'Work_files')}], 'links':[{'label':'','target':''} for _ in range(3)], 'apps':{kind:{'path':'','visible':True} for kind in ('obsidian','pos','vpn')}}

def read_config(data):
    try:
        value=json.loads((data/'desktop-tools.json').read_text(encoding='utf-8'))
        return validate_config(value)
    except (OSError,ValueError,TypeError,KeyError):return defaults()

def folder_path(value):
    if not isinstance(value,str) or len(value)>1024 or any(c in value for c in '\x00\r\n"'):raise ValueError('Enter a Windows folder path.')
    value=ntpath.normpath(value.strip())
    if value.startswith(('\\\\?\\','\\\\.\\')):raise ValueError('Enter a normal Windows folder path.')
    if not (value.startswith('\\\\') and len(value.strip('\\').split('\\'))>=2 or len(value)>2 and value[1:3]==':\\'):
        raise ValueError('Enter a full folder path, such as C:\\Users\\admin\\Documents or \\\\SERVER\\Shared.')
    return value

def link_target(value):
    if not value:return ''
    if not isinstance(value,str) or len(value)>2048 or any(c in value for c in '\x00\r\n"'):raise ValueError('Enter a website or folder path.')
    value=value.strip();parts=urlsplit(value)
    if parts.scheme in ('http','https'):
        if not parts.hostname or parts.username or parts.password:raise ValueError('Enter a normal website address.')
        return value
    return folder_path(value)

def app_path(value):
    if not value:return ''
    if not isinstance(value,str):raise ValueError('Choose a Windows app (.exe file).')
    value=value.strip()
    if value.startswith('"') and value.endswith('"'):value=value[1:-1]
    value=folder_path(value)
    if ntpath.splitext(value)[1].casefold()!='.exe':raise ValueError('Choose a Windows app (.exe file).')
    return value

def validate_config(value):
    if not isinstance(value,dict):raise ValueError('Invalid settings.')
    roots=value.get('roots',[]);links=value.get('links',[])
    if not isinstance(roots,list) or len(roots)>8 or not isinstance(links,list) or len(links)>3:raise ValueError('Too many folders or shortcuts.')
    clean_roots=[];seen=set()
    for r in roots:
        path=folder_path(r['path']);label=str(r.get('label','')).strip()[:60] or ntpath.basename(path) or path
        if path.casefold() not in seen:clean_roots.append({'label':label,'path':path});seen.add(path.casefold())
    clean_links=[]
    for r in links:
        target=link_target(r.get('target',''));label=str(r.get('label','')).strip()[:40]
        if target and not label:raise ValueError('Add a shortcut name.')
        clean_links.append({'label':label,'target':target})
    apps=value.get('apps',{})
    if not isinstance(apps,dict):raise ValueError('Invalid app settings.')
    clean_apps={}
    for kind in ('obsidian','pos','vpn'):
        entry=apps.get(kind,{})
        if not isinstance(entry,dict) or not isinstance(entry.get('visible',True),bool):raise ValueError('Invalid app settings.')
        clean_apps[kind]={'path':app_path(entry.get('path','')),'visible':entry.get('visible',True)}
    return {'roots':clean_roots,'links':(clean_links+[{'label':'','target':''} for _ in range(3)])[:3], 'apps':clean_apps}

def save_config(data,value):
    clean=validate_config(value);data.mkdir(exist_ok=True)
    with CONFIG_LOCK:
        temporary=data/'desktop-tools.tmp';temporary.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(data/'desktop-tools.json')
    return clean

def registry_app_paths(names):
    """Read installed-app registrations only; never change Windows settings."""
    if os.name!='nt':return []
    import winreg
    found=[]
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY):
            for name in names:
                try:
                    with winreg.OpenKey(hive,'Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\'+name,0,winreg.KEY_READ|view) as key:
                        value,_=winreg.QueryValueEx(key,None)
                    found.append(Path(app_path(os.path.expandvars(value))))
                except (OSError,ValueError,TypeError):pass
    return found

def resolve_app(kind,config):
    custom=config['apps'][kind]['path']
    if custom:return Path(custom) if Path(custom).is_file() else None
    program_roots=[Path(os.environ.get(name,fallback)) for name,fallback in (
        ('PROGRAMFILES',r'C:\Program Files'),('PROGRAMFILES(X86)',r'C:\Program Files (x86)'),('ProgramW6432',r'C:\Program Files'))]
    if kind=='pos':
        # A dated POS executable varies by workstation. Do not guess among versions.
        order=Path(os.environ.get('SystemDrive','C:')+'\\Order')
        try:candidates=[p for p in order.glob('sales*.exe') if p.is_file()]
        except OSError:candidates=[]
        return candidates[0] if len(candidates)==1 else None
    if kind=='vpn':
        names=('vpncmgr_x64.exe','vpncmgr.exe')
        candidates=registry_app_paths(names)+[base/'SoftEther VPN Client'/name for base in program_roots for name in names]
    elif kind=='obsidian':
        local=Path(os.environ.get('LOCALAPPDATA',''))
        candidates=registry_app_paths(('Obsidian.exe',))+[local/'Programs/Obsidian/Obsidian.exe',local/'Obsidian/Obsidian.exe']+[base/'Obsidian/Obsidian.exe' for base in program_roots]
    else:return None
    return next((p for p in candidates if p.is_file()),None)

def pick_app_file():
    """Windows common file dialog, with no command shell or app execution."""
    class OpenFileName(ctypes.Structure):
        _fields_=[('lStructSize',wintypes.DWORD),('hwndOwner',wintypes.HWND),('hInstance',wintypes.HINSTANCE),
            ('lpstrFilter',wintypes.LPCWSTR),('lpstrCustomFilter',wintypes.LPWSTR),('nMaxCustFilter',wintypes.DWORD),
            ('nFilterIndex',wintypes.DWORD),('lpstrFile',wintypes.LPWSTR),('nMaxFile',wintypes.DWORD),
            ('lpstrFileTitle',wintypes.LPWSTR),('nMaxFileTitle',wintypes.DWORD),('lpstrInitialDir',wintypes.LPCWSTR),
            ('lpstrTitle',wintypes.LPCWSTR),('Flags',wintypes.DWORD),('nFileOffset',wintypes.WORD),
            ('nFileExtension',wintypes.WORD),('lpstrDefExt',wintypes.LPCWSTR),('lCustData',wintypes.LPARAM),
            ('lpfnHook',ctypes.c_void_p),('lpTemplateName',wintypes.LPCWSTR),('pvReserved',ctypes.c_void_p),
            ('dwReserved',wintypes.DWORD),('FlagsEx',wintypes.DWORD)]
    dialog=ctypes.WinDLL('comdlg32',use_last_error=True)
    dialog.GetOpenFileNameW.argtypes=[ctypes.POINTER(OpenFileName)];dialog.GetOpenFileNameW.restype=wintypes.BOOL
    dialog.CommDlgExtendedError.restype=wintypes.DWORD
    buffer=ctypes.create_unicode_buffer(32768)
    request=OpenFileName();request.lStructSize=ctypes.sizeof(request)
    request.lpstrFilter='Windows apps (*.exe)\0*.exe\0\0';request.nFilterIndex=1
    request.lpstrFile=ctypes.cast(buffer,wintypes.LPWSTR);request.nMaxFile=len(buffer)
    request.lpstrInitialDir=os.environ.get('SystemDrive','C:')+'\\'
    request.lpstrTitle='Choose app / 앱 선택';request.lpstrDefExt='exe'
    # Explorer, file/path must exist, keep working directory, resizable, no Recent entry.
    request.Flags=0x00080000|0x00001000|0x00000800|0x00000008|0x00800000|0x02000000
    if dialog.GetOpenFileNameW(ctypes.byref(request)):return buffer.value
    if dialog.CommDlgExtendedError():raise ValueError('Could not open the app picker. Paste the app file path instead.')
    return ''

def choose_app_file():
    """Choose a file only; saved settings are changed after the user presses Save."""
    if os.name!='nt':raise ValueError('App selection is available in the Windows app.')
    path=app_path(pick_app_file())
    if path and not Path(path).is_file():raise ValueError('The selected app file is unavailable.')
    return {'path':path,'cancelled':not bool(path)}

def open_desktop_app(executable,missing_message):
    executable=Path(executable)
    if not executable.is_file():raise ValueError(missing_message)
    user32=ctypes.WinDLL('user32',use_last_error=True);kernel32=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel32.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel32.OpenProcess.restype=wintypes.HANDLE
    kernel32.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel32.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)];user32.GetWindowThreadProcessId.restype=wintypes.DWORD
    user32.IsWindowVisible.argtypes=[wintypes.HWND];user32.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];user32.SetForegroundWindow.argtypes=[wintypes.HWND]
    found=[]
    @ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def visit(window,unused):
        if not user32.IsWindowVisible(window):return True
        pid=wintypes.DWORD();user32.GetWindowThreadProcessId(window,ctypes.byref(pid));handle=kernel32.OpenProcess(0x1000,False,pid.value)
        if not handle:return True
        try:
            size=wintypes.DWORD(32768);buffer=ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle,0,buffer,ctypes.byref(size)) and buffer.value.casefold()==str(executable).casefold():found.append(window);return False
        finally:kernel32.CloseHandle(handle)
        return True
    user32.EnumWindows.argtypes=[type(visit),wintypes.LPARAM];user32.EnumWindows(visit,0)
    if found:
        user32.ShowWindow(found[0],9);user32.SetForegroundWindow(found[0]);return
    subprocess.Popen([str(executable)],cwd=str(executable.parent),close_fds=True)

def launch(target):
    os.startfile(target)

def explorer(path):
    if not path.startswith('shell:'):path=path.rstrip('\\')+'\\'
    subprocess.Popen([str(Path(os.environ.get('WINDIR','C:\\Windows'))/'explorer.exe'),path],close_fds=True)

def start_search(data,payload):
    query=str(payload.get('query','')).strip()[:160]
    if len(query)<2:raise ValueError('Type at least two characters.')
    config=read_config(data);scope=payload.get('scope','all')
    roots=config['roots'] if scope=='all' else [r for i,r in enumerate(config['roots']) if str(i)==str(scope)]
    if not roots:raise ValueError('Add a search folder first.')
    if not WORKERS.acquire(blocking=False):raise ValueError('A folder search is still busy. Please try again shortly.')
    key=uuid.uuid4().hex
    with JOBS_LOCK:
        for old in [k for k,v in JOBS.items() if time.monotonic()-v['created']>600]:del JOBS[old]
        JOBS[key]={'created':time.monotonic(),'done':False,'results':[],'warnings':[]}
    def run():
        proc=None
        try:
            python=Path(sys.executable).with_name('python.exe')
            proc=subprocess.Popen([str(python if python.exists() else Path(sys.executable)),str(Path(__file__).resolve()),'--search-worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            out,_=proc.communicate(json.dumps({'query':query,'roots':roots},ensure_ascii=False).encode('utf-8'),timeout=12)
            if proc.returncode:raise ValueError('The folder search could not finish.')
            result=json.loads(out.decode('utf-8'))
        except subprocess.TimeoutExpired:
            proc.kill();proc.communicate();result={'results':[],'warnings':['A folder did not respond. Check its connection and try a smaller search folder.']}
        except Exception:
            result={'results':[],'warnings':['The folder search could not finish.']}
        finally:WORKERS.release()
        with JOBS_LOCK:JOBS[key].update(result,done=True)
    threading.Thread(target=run,daemon=True).start()
    return {'job':key}

def worker(payload):
    terms=payload['query'].casefold().split();results=[];warnings=[];count=0;started=time.monotonic();limited=False
    for root in payload['roots']:
        stack=[root['path']]
        while stack:
            if time.monotonic()-started>8 or count>=50000 or len(results)>=100:limited=True;break
            directory=stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        count+=1
                        if count%100==0 and (time.monotonic()-started>8 or count>=50000):limited=True;break
                        try:
                            if entry.is_symlink() or entry.name.casefold() in SKIP:continue
                            is_dir=entry.is_dir(follow_symlinks=False)
                            if is_dir:
                                # Do not traverse Windows junctions/reparse points into other locations.
                                if getattr(entry.stat(follow_symlinks=False),'st_file_attributes',0)&1024:continue
                                stack.append(entry.path)
                            if all(term in entry.name.casefold() for term in terms):
                                results.append({'name':entry.name,'path':entry.path,'folder':is_dir,'root':root['label'],'canOpen':is_dir or ntpath.splitext(entry.name)[1].casefold() in OPEN_TYPES})
                                if len(results)>=100:limited=True;break
                        except OSError:continue
            except OSError:
                if directory==root['path']:warnings.append('Folder unavailable: '+root['label'])
        if limited:break
    return {'results':results,'warnings':warnings,'limited':limited,'scanned':count}

def state(data):
    config=read_config(data)
    status={kind:{'found':bool(resolve_app(kind,config))} for kind in config['apps']}
    return {**config,'appStatus':status,'obsidianInstalled':status['obsidian']['found']}

def handle_get(handler,path,data):
    if path=='/local-api/tools':handler.reply(state(data));return True
    if path.startswith('/local-api/tools/search/'):
        key=path.rsplit('/',1)[-1]
        with JOBS_LOCK:job=JOBS.get(key);value={k:v for k,v in job.items() if k!='created'} if job else None
        handler.reply(value or {'error':'Search expired. Search again.'},200 if value else 404);return True
    return False

def handle_post(path,payload,data):
    if path=='/local-api/tools/config':
        save_config(data,payload);return state(data)
    if path=='/local-api/tools/search':return start_search(data,payload)
    if path=='/local-api/tools/choose-app':return choose_app_file()
    if path=='/local-api/tools/open':
        kind=payload.get('kind')
        if kind in ('obsidian','pos','vpn'):
            executable=resolve_app(kind,read_config(data))
            if not executable:return {'opened':False,'needsSetup':kind}
            open_desktop_app(executable,'The selected app file is unavailable.')
            return {'opened':True}
        if kind=='network':explorer('shell:NetworkPlacesFolder');return {'opened':True}
        if kind=='network-address':
            address=payload.get('address','').strip()
            if not address.startswith('\\\\') or address.startswith(('\\\\?\\','\\\\.\\')) or any(c in address for c in '\x00\r\n\"<>|?*:') or len(address)>1024:raise ValueError('Enter a network address such as \\\\COMPUTER.')
            if not address.strip('\\'):raise ValueError('Enter a computer name after the two backslashes.')
            explorer(address);return {'opened':True}
        if kind=='root':
            roots=read_config(data)['roots'];index=int(payload['index'])
            if not 0<=index<len(roots):raise ValueError('Choose a search folder.')
            explorer(roots[index]['path']);return {'opened':True}
        if kind=='link':
            links=read_config(data)['links'];index=int(payload['index'])
            if not 0<=index<len(links) or not links[index]['target']:raise ValueError('Set up this shortcut first.')
            target=links[index]['target']
            if urlsplit(target).scheme in ('http','https'):launch(target)
            elif ntpath.splitext(target)[1].casefold()=='.exe':open_desktop_app(app_path(target),'The selected app file is unavailable.')
            else:explorer(target)
            return {'opened':True}
        if kind=='result':
            with JOBS_LOCK:
                job=JOBS.get(payload.get('job'));index=int(payload['index'])
                if not job or not 0<=index<len(job['results']):raise ValueError('Search again to open this result.')
                result=job['results'][index]
            # A caller cannot pass an arbitrary command/path; only results from this session can open.
            if payload.get('showFolder'):explorer(ntpath.dirname(result['path']))
            elif result['folder']:explorer(result['path'])
            elif result['canOpen']:launch(result['path'])
            else:raise ValueError('Use Open folder to view this file in Explorer.')
            return {'opened':True}
        raise ValueError('Choose a valid desktop action.')
    raise ValueError('Unknown desktop action.')

if __name__=='__main__' and '--search-worker' in sys.argv:
    request=json.loads(sys.stdin.buffer.read().decode('utf-8'));sys.stdout.buffer.write(json.dumps(worker(request),ensure_ascii=False).encode('utf-8'))
