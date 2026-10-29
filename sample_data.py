"""Fictional onboarding samples, installed once for a new local data file."""
from datetime import datetime,timezone,timedelta
import json,calendar

def initialize_samples(db,root):
    db.execute('CREATE TABLE IF NOT EXISTS app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    if db.execute("SELECT 1 FROM app_metadata WHERE key='demo_initialized'").fetchone():return
    # Never seed examples over an existing user's records.
    if not db.execute('SELECT COUNT(*) FROM documents').fetchone()[0]:
        sample=json.loads((root/'demo-samples.json').read_text(encoding='utf-8'))
        today=datetime.now(timezone(timedelta(hours=9))).date();month=today.strftime('%Y-%m')
        docs={}
        for day in sample['days']:
            number=today.day if day['day']=='today' else min(int(day['day']),calendar.monthrange(today.year,today.month)[1])
            date=f'{month}-{number:02d}';key='work:'+date
            doc=docs.setdefault(key,{'id':key,'date':date,'kind':'day','calendar':'work','layers':[],'completedLayers':[]})
            doc['layers'].extend(day['tasks']);doc['completedLayers'].extend(day['completed']);doc['html']='<br><br>'.join(doc['layers'])
        for memo in sample['memos']:
            docs[memo['id']]={**memo,'kind':'memo','month':month}
        for doc in docs.values():
            db.execute('INSERT INTO documents(id,body,revision) VALUES(?,?,1)',(doc['id'],json.dumps(doc,ensure_ascii=False)))
    db.execute("INSERT INTO app_metadata(key,value) VALUES('demo_initialized','1')")
