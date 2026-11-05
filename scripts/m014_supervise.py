"""Bounded M014 stage launcher, with an independent outer process watchdog."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

output=Path(sys.argv[1]).resolve()
budget=float(sys.argv[2])
command=sys.argv[3:]
output.mkdir(parents=True,exist_ok=False)
code='''from neuromancer.supervisor import Deadline,supervise
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);r=supervise(json.loads(sys.argv[3]),p/'supervision',Deadline.after(float(sys.argv[2])),workers=1)
(p/'returned.json').write_text(json.dumps(r,indent=2))
raise SystemExit(0 if r['status']=='COMPLETED' else 1)
'''
process=subprocess.Popen([sys.executable,'-c',code,str(output),str(budget),json.dumps([command])],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
intervened=False
try:
    stdout,stderr=process.communicate(timeout=budget+5)
except subprocess.TimeoutExpired:
    intervened=True
    # Only terminate process groups explicitly owned by this stage.
    for filename in ['progress.json','terminal.json']:
        path=output/'supervision'/filename
        if path.exists():
            record=json.loads(path.read_text())
            for worker in record.get('workers',[]):
                if 'pgid' in worker:
                    try:os.killpg(worker['pgid'],signal.SIGKILL)
                    except ProcessLookupError:pass
    os.killpg(process.pid,signal.SIGKILL)
    stdout,stderr=process.communicate(timeout=2)
(output/'outer_stdout.log').write_bytes(stdout)
(output/'outer_stderr.log').write_bytes(stderr)
(output/'outer.json').write_text(json.dumps(dict(watchdog_intervened=intervened,returncode=process.returncode)))
raise SystemExit(1 if intervened else process.returncode)
