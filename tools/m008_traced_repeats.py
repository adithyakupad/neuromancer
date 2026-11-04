"""Frozen diagnostic conditions; every trial retained regardless of status."""
import json,os,signal,subprocess,sys,time
from pathlib import Path
from neuromancer.supervisor import Deadline,atomic_json

def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);d=Deadline.after(900);rows=[]
 conditions=['ordinary']*20+['immediate']*3+[c for c in ('wake_delay','parent_delay','import_delay','persist_delay') for _ in range(3)]
 atomic_json(out/'manifest.json',dict(conditions=conditions,clock_id=d.clock_id,deadline_ns=d.end_ns))
 for i,condition in enumerate(conditions):
  d.check();folder=out/f'{i:02d}_{condition}';began=time.monotonic_ns();watchdog=False
  with (out/f'{i:02d}.log').open('wb') as log:
   proc=subprocess.Popen([sys.executable,'tools/m008_trial.py',str(folder),condition],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   try:proc.wait(timeout=min(12,d.remaining()))
   except subprocess.TimeoutExpired:
    watchdog=True
    for f in folder.rglob('pid.json'):
     try:os.killpg(json.loads(f.read_text())['pgid'],signal.SIGKILL)
     except ProcessLookupError:pass
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proc.wait(timeout=1)
  rows.append(dict(index=i,condition=condition,returncode=proc.returncode,watchdog=watchdog,elapsed_ns=time.monotonic_ns()-began));atomic_json(out/'outer.json',rows)
  if watchdog or proc.returncode:raise RuntimeError('Diagnostic worker/cleanup failure; preserve all records')
 atomic_json(out/'complete.json',dict(trials=len(rows),remaining_s=d.remaining()))
if __name__=='__main__':main()
