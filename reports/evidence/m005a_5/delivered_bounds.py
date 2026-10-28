"""Prespecified delivered-action bound occupancy, distinct from PI clipping flags."""
import csv,json
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline
Deadline.from_environment().check();r=Path(__file__).resolve().parent;rows=[]
for folder in sorted((r/'confirmation').glob('n*_r*')):
 m=json.loads((folder/'trial.json').read_text())
 for b in m['branches']:
  u=np.load(folder/f"{b['condition']}_{b['controller']}.npz")['delivered'];q=u[:,0]
  np.testing.assert_array_equal(q,u[:,2]);assert (u[:,[1,3]]==0).all()
  low=float(np.mean(q==0));high=float(np.mean(q==120));budget=float(np.mean(u.sum(1)==240))
  assert budget==high
  if b['controller']=='ZERO':assert low==1 and high==0
  if b['controller']=='MAX':assert high==1597/1600 and low==0 # 30,60,90pA then120.
  rows.append(dict(network=m['network_id'],replicate=m['replicate_id'],condition=b['condition'],controller=b['controller'],dose_zero_fraction=low,dose_max_fraction=high,dose_either_bound_fraction=low+high,total_current_budget_fraction=budget))
assert len(rows)==160
with (r/'delivered_bound_occupancy.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(r/'delivered_bounds_verification.json').write_text(json.dumps(dict(status='PASS',branches=160,analytic_checks='C02 identity, MAX1597/1600ticks at120pA, ZEROallzero, totalbudget equivalence',interpretation='Prespecified descriptive occupancy; not a changed gate or PI clipping statistic'),indent=2)+'\n')
Deadline.from_environment().check()
