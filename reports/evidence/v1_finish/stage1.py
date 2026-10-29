"""Original regression/clock qualification under a shared preflight deadline."""
import json,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise
from neuromancer.clocks import get_clock,clock_domain
r=Path(__file__).resolve().parent
d=Deadline.after(1200);samples=[get_clock().sample() for _ in range(1000)]
(r/'stage1_clock.json').write_text(json.dumps(dict(clock_id=clock_domain(),samples=1000,first=samples[0],last=samples[-1]),indent=2)+'\n')
x=supervise([[sys.executable,'-m','pytest','-q','--basetemp='+str(r/'stage1_fixtures'),'--junitxml='+str(r/'stage1_tests.xml')]],r/'stage1_supervision',d,workers=1)
assert x['status']=='COMPLETED'
