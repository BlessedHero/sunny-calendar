"""Require project-only commit identity before creating public downloads."""
import subprocess,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
allowed={('Sunny Calendar contributors','sunny-calendar@local.invalid'),('Sunny Calendar project','sunny-calendar@local.invalid'),('github-actions[bot]','41898282+github-actions[bot]@users.noreply.github.com')}
records=subprocess.check_output(['git','-C',str(root),'log','HEAD','--format=%an%x09%ae%x09%cn%x09%ce'],text=True).splitlines()
for row in records:
    author,mail,committer,committer_mail=row.split('\t')
    if (author,mail) not in allowed or (committer,committer_mail) not in allowed:
        raise SystemExit('Release blocked: use the project-only Git author identity and a clean public history. Personal author details must not be published.')
print('Public commit identity check passed.')
