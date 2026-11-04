"""Independent excitation/design spectra, costs, baselines and interval auditor."""
import csv,json
from pathlib import Path
import numpy as np
r=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
designs=read(r/'confirmation_analysis/excitation.json');summary=read(r/'confirmation_analysis/summary.json');sec=read(r/'confirmation_analysis/secondary.json')
rows=list(csv.DictReader((r/'confirmation_analysis/metrics.csv').open()))
count=0
for folder in (r/'confirmation').glob('n*_r*'):
 m=read(folder/'trial.json');n,k=m['network_id'],m['replicate_id']
 assert m['engine']['config']['trial_id']==f'm005a-n{n}-r{k}'
 for b in m['branches']:
  name,c=b['controller'],b['condition'];d=dict(np.load(folder/f'{c}_{name}.npz'));u=d['delivered']
  assert np.array_equal(d['requested'],u)
  for window,start in [('full',0),('last16',800)]:
   a=u[start:];z=(a-a.mean(0))/np.maximum(a.std(0),1)
   # Independent explicit row/lag construction, not scorer's column slicing.
   x=np.array([[1.]+[float(v) for lag in range(10) for v in z[t-lag]] for t in range(9,len(z))])
   sv=np.linalg.svd(x,compute_uv=False);positive=sv[sv>max(x.shape)*np.finfo(float).eps*sv[0]]
   expected=next(v for v in designs if (v['network'],v['replicate'],v['condition'],v['controller'],v['window'])==(n,k,c,name,window))
   assert expected['rank']==len(positive) and expected['features']==41
   np.testing.assert_allclose(expected['singular_values'],sv,rtol=1e-10,atol=1e-11)
   assert expected['full_condition'] is None # C02 channels identical and two channels zero.
   np.testing.assert_allclose(expected['positive_condition'],positive[0]/positive[-1],rtol=1e-10)
   count+=1
  full=next(v for v in rows if int(v['network'])==n and int(v['replicate'])==k and v['condition']==c and v['controller']==name and v['window']=='full')
  prefix=np.load(folder/'prefix.npz')['delivered'];charge=50*.02*(u.sum()+prefix.sum())
  np.testing.assert_allclose(float(full['total_charge_pC']),charge,rtol=1e-12)
  assert int(full['fallback_decisions'])==int(d['decisions'][:,6].sum())
for name in summary['models']:
 for c,w in [('STATIC','stationary'),('LOSS','late')]:
  values=np.array([np.mean([float(v['mae_hz']) for v in rows if int(v['network'])==n and v['condition']==c and v['controller']==name and v['window']==w]) for n in range(10)])
  rng=np.random.Generator(np.random.PCG64(20261025));ci=np.quantile(values[rng.integers(0,10,(10000,10))].mean(1),[.025,.975])
  np.testing.assert_allclose(summary['models'][name][c]['ci_hz'],ci,rtol=1e-12)
  np.testing.assert_allclose(summary['models'][name][c]['network_mae_hz'],values,rtol=1e-12)
assert count==320
(r/'extra_verification.json').write_text(json.dumps(dict(status='PASS',designs=count,models=4,network_bootstrap_intervals=8,charge_branches=160,notes='Independent construction; rank deficiency disclosed, no full-channel persistent-excitation claim'),indent=2)+'\n')
