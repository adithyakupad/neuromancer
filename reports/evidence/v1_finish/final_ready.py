"""Fresh prospective preflight of prepared source; unchanged1,200s allowance."""
import json,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json
r=Path(__file__).resolve().parent;d=Deadline.after(1200);atomic_json(r/'freeze_deadline.json',dict(end_ns=d.end_ns,clock_id=d.clock_id))
commands=[[sys.executable,'-m','pytest','-q','--basetemp='+str(r/'ready_test_fixtures'),'--junitxml='+str(r/'ready_tests.xml')],[sys.executable,str(r/'verify_study.py'),str(r/'runner_smoke'),str(r/'ready_runner_verification.json')],[sys.executable,str(r/'freeze_acquisition.py')]]
x=supervise(commands,r/'ready_supervision',d,workers=1);print(x['status']);assert x['status']=='COMPLETED'
