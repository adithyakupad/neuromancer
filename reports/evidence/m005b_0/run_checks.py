"""Single qualified deadline, synthetic design checks and historical regressions."""
import json,os,signal,subprocess,sys,time
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json
from neuromancer.clocks import now_ns
R=Path(__file__).resolve().parent

def inner():
 d=Deadline.from_environment();commands=[
 [sys.executable,'-m','pytest','-q',str(R/'test_design.py'),'--basetemp='+str(R/'synthetic_fixtures'),'--junitxml='+str(R/'synthetic_tests.xml')],
 [sys.executable,'-m','pytest','-q','--basetemp='+str(R/'regression_fixtures'),'--junitxml='+str(R/'regression_tests.xml')],
 [sys.executable,str(R/'benchmark.py')]]
 result=supervise(commands,R/'supervision',d,workers=1);print(result['status']);assert result['status']=='COMPLETED'

def capture():
 d=Deadline.after(900);start=now_ns();env=dict(os.environ,NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id)
 with (R/'checks.log').open('wb') as log:
  p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--inner'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=p.wait(timeout=905)
  except subprocess.TimeoutExpired:
   state=R/'supervision/progress.json'
   if state.exists():
    for w in json.loads(state.read_text())['workers']:
     if w.get('pgid'):
      try:os.killpg(w['pgid'],signal.SIGKILL)
      except ProcessLookupError:pass
   os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=1);code=-9
 finish=now_ns();record=dict(status='PASS' if code==0 and finish<=d.end_ns else 'HOLD',returncode=code,started_ns=start,finished_ns=finish,deadline_ns=d.end_ns,clock_id=d.clock_id,elapsed_s=(finish-start)/1e9)
 atomic_json(R/'closure.json',record);print(json.dumps(record));assert record['status']=='PASS'
if __name__=='__main__':inner() if sys.argv[1:]==['--inner'] else capture()
