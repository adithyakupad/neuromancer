"""Native clock and immutable historical evidence qualification, no acquisition."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
from neuromancer.clocks import get_clock
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent
Deadline.from_environment().check()
p=json.loads((r/'preservation.json').read_text())
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in p['historical_sha256'].items())
selection=Path('reports/evidence/m005a_3/tuning_analysis/selection.json')
plan=json.loads((r/'plan.json').read_text())
assert hashlib.sha256(selection.read_bytes()).hexdigest()==plan['selection_sha256']
assert subprocess.check_output(['git','show',plan['selection_revision']+':'+str(selection)])==selection.read_bytes()
c=get_clock();samples=[c.sample() for _ in range(1000)]
child=json.loads(subprocess.check_output([sys.executable,'-c','from neuromancer.clocks import get_clock;import json;print(json.dumps(get_clock().sample()))'],text=True))
assert child['clock_id']==c.domain and child['continuous_ns']>=samples[-1]['continuous_ns']
assert all(b['continuous_ns']>=a['continuous_ns'] for a,b in zip(samples,samples[1:]))
(r/'preflight_native.json').write_text(json.dumps(dict(status='PASS',samples=1000,first=samples[0],last=samples[-1],child=child,physical_sleep='NOT_RUN',preserved=len(p['historical_sha256']),environment=dict(python=sys.version,clock=time.get_clock_info('monotonic').implementation)),indent=2)+'\n')
subprocess.run([sys.executable,str(r/'audit_original.py'),'reports/evidence/m005a_3'],check=True)
Deadline.from_environment().check()
