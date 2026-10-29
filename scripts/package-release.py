"""Package a reviewed clean Windows build. Never includes user data."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--source',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
subprocess.run([__import__('sys').executable,str(root/'scripts/check-release-privacy.py')],check=True)
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
seed=json.loads((root/'src/seed.json').read_text(encoding='utf-8'))
assert seed['docs']==[] and seed['review']==[],'Release seed must be empty'
files=[]
for folder in ('dist/client','runtime','licenses'):
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(root/name for name in ('Sunny Calendar Demo.exe','Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll','WebView2Loader.dll','calendar-icon.ico','start-calendar.py','calendar_updates.py','app-release.json','desktop_tools.py','sample_data.py','demo-samples.json','README.md','LICENSE','CHANGELOG.md'))
portable=out/f'Sunny-Calendar-Demo-Windows-{version}.zip'
with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED) as z:
    for path in files:
        assert path.is_file(),str(path)
        z.write(path,'Sunny Calendar Demo/'+path.relative_to(root).as_posix())
artifacts=[portable]
if args.source:
    assert not subprocess.check_output(['git','-C',str(root),'status','--porcelain']).strip(),'Commit reviewed source before packaging'
    source=out/f'Sunny-Calendar-Demo-Source-{version}.zip'
    subprocess.run(['git','-C',str(root),'archive','--format=zip','--prefix=Sunny-Calendar-Demo-Source/','--output='+str(source),'HEAD'],check=True)
    artifacts.append(source)
for artifact in artifacts:
    with zipfile.ZipFile(artifact) as z:
        for name in z.namelist():
            assert not any(part in name.split('/') for part in ('local-data','node_modules','.git','__pycache__'))
            assert not name.endswith(('.sqlite','.jpg','.lnk','.log'))
            if name.endswith(('.json','.jsx','.js','.py','.md','.txt','.html')):
                body=z.read(name).decode('utf-8-sig',errors='replace')
                # Obvious credential literals are never allowed in public packages.
                assert ('-----BEGIN '+'PRIVATE KEY-----') not in body
setup=out/'Sunny-Calendar-Setup.exe'
if setup.exists():artifacts.append(setup)
checks={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in artifacts}
(out/'SHA256SUMS.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in checks.items()),encoding='utf-8')
(out/f'Sunny-Calendar-Demo-{version}-checksums.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
