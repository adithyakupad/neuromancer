"""Deterministic M004 rescore/figures/derived archive, no neural runs or fitting."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

p=argparse.ArgumentParser();p.add_argument('--dev',required=True);p.add_argument('--dev-replay',required=True);p.add_argument('--validation',required=True);p.add_argument('--validation-replay',required=True)
p.add_argument('--selection',required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();base=Path(__file__).parent;began=time.perf_counter();common=['--dev',a.dev,'--dev-replay',a.dev_replay,'--validation',a.validation,'--validation-replay',a.validation_replay]
for script,args in [('analyze.py',[*common,'--selection',a.selection,'--output',str(a.output)]),('figures.py',['--analysis',str(a.output)]),
                    ('archive_oracle.py',[*common,'--analysis',str(a.output)]),('summary_tables.py',[*common,'--analysis',str(a.output)])]:
    subprocess.run([sys.executable,str(base/script),*args],check=True,stdout=subprocess.DEVNULL,timeout=900)
checks={}
for path in sorted(a.output.rglob('*')):
    if not path.is_file():continue
    relative=path.relative_to(a.output);old=a.original/relative
    if relative==Path('comparison.json'):
        x=json.loads(path.read_text());y=json.loads(old.read_text());x.pop('analysis_wall_s');y.pop('analysis_wall_s');assert x==y
        checks[str(relative)]='All scientific fields identical; measured runtime excluded'
    else:
        assert path.read_bytes()==old.read_bytes(),str(relative)
        checks[str(relative)]=hashlib.sha256(path.read_bytes()).hexdigest()
result=dict(status='PASS',files=len(checks),checks=checks,wall_s=time.perf_counter()-began)
(a.original/'reproducibility.json').write_text(json.dumps(result,indent=2)+'\n');print('Deterministic reanalysis PASS',len(checks),'files')
