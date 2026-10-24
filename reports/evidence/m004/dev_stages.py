"""Wait bounded acquisition, then replay and tune from public development streams."""
import json
from pathlib import Path
import subprocess
import sys
import time
base=Path(__file__).parent;raw=Path('runs/m004-dev-01');start=time.monotonic()
while not (raw/'summary.json').exists():
    if time.monotonic()-start>3600:raise SystemExit('No complete acquisition within budget')
    time.sleep(5)
assert json.loads((raw/'summary.json').read_text())['status']=='complete'
ledger=[]
for script,args in [('replay.py',['--raw',str(raw),'--output','runs/m004-dev-replay-01']),
                    ('select_models.py',['--raw',str(raw),'--replay','runs/m004-dev-replay-01','--output',str(base/'selection.json')])]:
    command=[sys.executable,str(base/script),*args];began=time.perf_counter()
    with (base/(script.removesuffix('.py')+'_dev.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    ledger.append(dict(command=command,returncode=r.returncode,wall_s=time.perf_counter()-began));(base/'dev_stages.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(script,ledger[-1],flush=True)
    if r.returncode:raise SystemExit('Failed stage preserved')
