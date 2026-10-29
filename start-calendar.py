"""Sunny Calendar: private loopback-only launcher and local data file."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import argparse,json,sqlite3,threading,time,urllib.request,webbrowser,re,importlib.util

ROOT=Path(__file__).resolve().parent
_tools_spec=importlib.util.spec_from_file_location('sunny_desktop_tools',ROOT/'desktop_tools.py')
DESKTOP_TOOLS=importlib.util.module_from_spec(_tools_spec);_tools_spec.loader.exec_module(DESKTOP_TOOLS)
_sample_spec=importlib.util.spec_from_file_location('sunny_sample_data',ROOT/'sample_data.py')
SAMPLE_DATA=importlib.util.module_from_spec(_sample_spec);_sample_spec.loader.exec_module(SAMPLE_DATA)
PORT=4176
URL=f'http://127.0.0.1:{PORT}/'
DATA=ROOT/'local-data'
LOCK=threading.Lock()
ALLOWED={f'127.0.0.1:{PORT}',f'localhost:{PORT}'}
DOC_ID=re.compile(r'^(work:\d{4}-\d{2}-\d{2}|reference:\d{4}-\d{2}|memo:[a-zA-Z0-9-]+)$')

def connection():
    db=sqlite3.connect(DATA/'calendar.sqlite',timeout=15)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, body TEXT NOT NULL, revision INTEGER NOT NULL)')
    SAMPLE_DATA.initialize_samples(db,ROOT)
    return db

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'dist/client'),**kwargs)
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; frame-ancestors 'none'")
        super().end_headers()
    def valid_host(self):
        if self.headers.get('Host','') not in ALLOWED:self.send_error(403);return False
        return True
    def reply(self,value,status=200):
        b=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if not self.valid_host():return
        if DESKTOP_TOOLS.handle_get(self,self.path,DATA):return
        if self.path=='/local-api/status':self.reply({'app':'Sunny Calendar','storage':'local-file','version':1,'edition':'clean-test'});return
        if self.path=='/local-api/documents':
            with LOCK,connection() as db:
                records=[]
                for body,rev in db.execute('SELECT body,revision FROM documents'):
                    value=json.loads(body);value['_revision']=rev;records.append(value)
            self.reply(records);return
        super().do_GET()
    def do_POST(self):
        if not self.valid_host():return
        if self.path!='/local-api/documents' and self.path not in {'/local-api/tools/config','/local-api/tools/search','/local-api/tools/open'}:self.send_error(404);return
        origin=self.headers.get('Origin','')
        if origin not in {f'http://{h}' for h in ALLOWED} or not self.headers.get('Content-Type','').startswith('application/json'):
            self.send_error(403);return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=30_000_000:raise ValueError('Size')
            if self.path.startswith('/local-api/tools/'):
                if n>32768:raise ValueError('Desktop settings are too large.')
                payload=json.loads(self.rfile.read(n))
                if not isinstance(payload,dict):raise ValueError('Invalid settings.')
                self.reply(DESKTOP_TOOLS.handle_post(self.path,payload,DATA));return
            payload=json.loads(self.rfile.read(n));doc=payload['doc'];key=doc['id'];expected=int(payload['expectedRevision'])
            if not isinstance(key,str) or not DOC_ID.fullmatch(key) or not isinstance(doc.get('html'),str):raise ValueError('Document')
            doc.pop('_revision',None)
            with LOCK,connection() as db:
                row=db.execute('SELECT revision FROM documents WHERE id=?',(key,)).fetchone();current=row[0] if row else 0
                if current!=expected:self.reply({'error':'changed-in-another-window'},409);return
                rev=current+1
                db.execute('INSERT INTO documents(id,body,revision) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body,revision=excluded.revision',(key,json.dumps(doc,ensure_ascii=False),rev))
            self.reply({'revision':rev})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as error:self.reply({'error':str(error) if self.path.startswith('/local-api/tools/') else 'Invalid local note'},400)
        except Exception:self.reply({'error':'Could not open this item. Check that the app or folder is available.' if self.path.startswith('/local-api/tools/') else 'Local save failed'},500)

def running():
    try:
        with urllib.request.urlopen(URL+'local-api/status',timeout=1) as r:return json.load(r).get('edition')=='clean-test'
    except Exception:return False

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--no-open',action='store_true');args=parser.parse_args()
    if running():
        if not args.no_open:webbrowser.open(URL)
    else:
        DATA.mkdir(exist_ok=True)
        if not (ROOT/'dist/client/index.html').exists():raise SystemExit('Build files are missing. Please restore the Sunny Calendar folder.')
        try:
            server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
        except OSError:
            if running():
                if not args.no_open:webbrowser.open(URL)
                raise SystemExit(0)
            if not args.no_open:
                import ctypes
                ctypes.windll.user32.MessageBoxW(None,'Sunny Calendar could not open because another local app is using its address. Close that app, then try again. Your saved notes are safe.','Sunny Calendar',16)
            raise SystemExit('Local port 4176 is already in use.')
        if not args.no_open:
            threading.Timer(.5,lambda:webbrowser.open(URL)).start()
        print('Sunny Calendar is running locally on '+URL,flush=True)
        server.serve_forever()
