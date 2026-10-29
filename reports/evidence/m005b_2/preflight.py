"""Bounded M005B.2 preflight only; no scientific acquisition entry point."""
import json,os,signal,subprocess,sys
from pathlib import Path
from neuromancer.clocks import now_ns
from neuromancer.supervisor import Deadline,supervise,atomic_json
R=Path(__file__).resolve().parent

def inner():
 d=Deadline.from_environment();commands=[
 [sys.executable,'-m','pytest','-q','--basetemp='+str(R/'preflight_fixtures'),'--junitxml='+str(R/'preflight_tests.xml')],
 [sys.executable,str(R/'readiness.py')]]
 out=supervise(commands,R/'supervision',d,workers=1);assert out['status']=='COMPLETED'

def main():
 d=Deadline.after(1200);start=now_ns();env=dict(os.environ,NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id)
 with (R/'run.log').open('wb') as log:
  p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--inner'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=p.wait(timeout=1205)
  except subprocess.TimeoutExpired:
   progress=R/'supervision/progress.json'
   if progress.exists():
    for w in json.loads(progress.read_text())['workers']:
     if w.get('pgid'):
      try:os.killpg(w['pgid'],signal.SIGKILL)
      except ProcessLookupError:pass
   os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=1);code=-9
 finish=now_ns();atomic_json(R/'closure.json',dict(status='PREFLIGHT_COMPLETE_READINESS_HOLD' if code==0 and finish<d.end_ns else 'PARTIAL',returncode=code,started_ns=start,finished_ns=finish,deadline_ns=d.end_ns,clock_id=d.clock_id,wall_s=(finish-start)/1e9));assert code==0
if __name__=='__main__':inner() if sys.argv[1:]==['--inner'] else main()
