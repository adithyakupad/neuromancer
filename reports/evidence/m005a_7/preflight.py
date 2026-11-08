"""Clock, history and frozen scientific source preflight."""
import hashlib,json,subprocess,sys
from pathlib import Path
from neuromancer.clocks import get_clock
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;Deadline.from_environment().check();history=json.loads((r/'preservation.json').read_text())['historical_sha256'];assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in history.items())
p=json.loads((r/'plan.json').read_text());selection=Path('reports/evidence/m005a_3/tuning_analysis/selection.json');assert hashlib.sha256(selection.read_bytes()).hexdigest()==p['selection_sha256'];assert subprocess.check_output(['git','show',p['selection_revision']+':'+str(selection)])==selection.read_bytes()
c=get_clock();samples=[c.sample() for _ in range(1000)];child=json.loads(subprocess.check_output([sys.executable,'-c','from neuromancer.clocks import get_clock;import json;print(json.dumps(get_clock().sample()))'],text=True));assert child['clock_id']==c.domain and child['continuous_ns']>=samples[-1]['continuous_ns']
assert all(b['continuous_ns']>=a['continuous_ns'] for a,b in zip(samples,samples[1:]))
assert {tuple(v) for v in p['pairs']}=={(n,k) for n in range(10) for k in (45,46)}
(r/'preflight_native.json').write_text(json.dumps(dict(status='PASS',first=samples[0],last=samples[-1],child=child,historical_files=len(history),frozen_controller=True,new_noise=[45,46]),indent=2)+'\n');Deadline.from_environment().check()
