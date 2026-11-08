"""Bind independently verified numerical gates to full execution requirements."""
import csv,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from neuromancer.supervisor import Deadline
deadline=Deadline.from_environment();deadline.check()
r=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
s=read(r/'confirmation_analysis/summary.json');plan=read(r/'plan.json')
for f in ('resource_verification.json','confirmation_verification.json','causality_verification.json','repeat_verification.json','replay_fixture/verification.json','extra_verification.json'):
    assert read(r/f)['status']=='PASS',f
for stage in ('preflight','verification'):
    t=read(r/f'{stage}_supervision/terminal.json');assert t['status']=='COMPLETED' and t['cleanup_verified']
    assert t['finished_ns']<=t['deadline_ns']
counts={}
for f in ('preflight_tests.xml','final_tests.xml'):
    suites=list(ET.parse(r/f).getroot().iter('testsuite'))
    assert all(int(t.attrib.get('failures',0))+int(t.attrib.get('errors',0))==0 for t in suites)
    counts[f]=sum(int(t.attrib['tests']) for t in suites)
assert counts['preflight_tests.xml']==counts['final_tests.xml']==144
rows=list(csv.DictReader((r/'confirmation_analysis/metrics.csv').open()))
base=[x for x in rows if x['window']=='full'];assert len(base)==160
fallbacks=sum(int(x['fallback_decisions']) for x in base)
violations=sum(b['audit']['violations'] for p in (r/'confirmation').glob('n*_r*/trial.json') for b in read(p)['branches'])
stationary=bool(s['stationary_pass'] and fallbacks==0 and violations==0);loss=bool(s['recovery_pass'] and fallbacks==0 and violations==0)
per=[]
for n in range(10):
 for k in (41,42):
  for condition,window in [('STATIC','stationary'),('LOSS','late')]:
   def get(name,key,w=window):
    v=[x for x in rows if int(x['network'])==n and int(x['replicate'])==k and x['condition']==condition and x['controller']==name and x['window']==w];assert len(v)==1;return float(v[0][key])
   per.append(dict(network=n,replicate=k,session='original' if [n,k] in plan['reused'] else 'continuation',condition=condition,pi_mae_hz=get('PI10_5','mae_hz'),fixed_mae_hz=get('FIXED','mae_hz'),zero_mae_hz=get('ZERO','mae_hz'),pi_bias_hz=get('PI10_5','bias_hz'),authority_hz=get('MAX','rate_hz','late')-get('ZERO','rate_hz','late'),target_hz=get('ZERO','target_hz'),noise_hz=get('ZERO','noise_hz')))
with (r/'per_replicate_errors.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
result=dict(execution='PASS',scientific='PASS' if stationary and loss else 'FAIL',stationary='PASS' if stationary else 'FAIL',recovery='PASS' if loss else 'FAIL',m005b='READY' if stationary and loss else 'HOLD',selected='PI10_5',selection_revision=plan['selection_revision'],amendment_revision='2781aa8556e77494598ac5a6dc37d4421cacdd7e',acquisition_revision=read(r/'acquisition_launch.json')['head'],trials=20,branches=160,reused=3,new=17,fallback_decisions=fallbacks,constraint_violations=violations,tests=counts,original_resource_failures='UNCHANGED',clock_stop='UNCHANGED',no_new_mission_authorized=True)
(r/'decision.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

deadline.check()
