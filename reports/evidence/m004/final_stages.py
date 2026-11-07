"""Bounded validation replay/evaluation after committed development selection."""
import json
from pathlib import Path
import subprocess
import sys
import time
base=Path(__file__).parent;raw=Path('runs/m004-validation-01');start=time.monotonic()
while not (raw/'summary.json').exists():
    if time.monotonic()-start>1500:raise SystemExit('Validation acquisition budget exceeded')
    time.sleep(5)
assert json.loads((raw/'summary.json').read_text())['status']=='complete'
common=['--dev','runs/m004-dev-01','--dev-replay','runs/m004-dev-replay-01','--validation',str(raw),'--validation-replay','runs/m004-validation-replay-01','--selection',str(base/'selection.json')]
commands=[('replay.py',['--raw',str(raw),'--output','runs/m004-validation-replay-01']),
 ('verify.py',['--raw',str(raw),'--replay','runs/m004-validation-replay-01','--output',str(base/'validation_verification.json')]),
 ('analyze.py',[*common,'--output','runs/m004-analysis-01']),
 ('verify_analysis.py',[*common,'--analysis','runs/m004-analysis-01','--output',str(base/'analysis_verification.json')]),
 ('figures.py',['--analysis','runs/m004-analysis-01'])]
ledger=[]
for script,args in commands:
    command=[sys.executable,str(base/script),*args];began=time.perf_counter()
    with (base/(script.removesuffix('.py')+'_final.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    ledger.append(dict(command=command,returncode=r.returncode,wall_s=time.perf_counter()-began));(base/'final_stages.json').write_text(json.dumps(ledger,indent=2)+'\n');print(script,ledger[-1],flush=True)
    if r.returncode:raise SystemExit('Failed stage preserved; downstream scoring stopped')
