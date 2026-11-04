"""Prespecified repeat resolving observed OS latency variation; no variant search."""
import argparse,json,time,types
from pathlib import Path
import numpy as np
from neuromancer.predictive_planner import plan
from neuromancer.supervisor import Deadline,atomic_json
from v1_1 import fixture,measured
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();
if args.output.exists():raise FileExistsError(args.output)
args.output.parent.mkdir(parents=True,exist_ok=True)
module=types.ModuleType('neuromancer._latency_reference');module.__package__='neuromancer';snapshot=Path('docs/history/PLANNER_V1_SNAPSHOT.py');exec(compile(snapshot.read_text(),str(snapshot),'exec'),module.__dict__);rec,*_=fixture();d=Deadline.from_environment();rows=[]
for repeat in range(4):
 for i in range(100):
  d.check();h=np.zeros((9,4));h[:,::2]=float(i*17%121);values={};outputs={}
  for name,f in ([('reference',module.plan),('optimized',plan)] if (i+repeat)%2==0 else [('optimized',plan),('reference',module.plan)]):
   result,t=measured(lambda:f(rec,rec['coef'],h,9.+i%3*.1,51_000_000));values[name]=t;outputs[name]=result
  for name in outputs['reference']:
   if name!='elapsed_ns':np.testing.assert_array_equal(outputs['reference'][name],outputs['optimized'][name],err_msg=name)
  rows.append(dict(repeat=repeat,index=i,**values))
summary={}
for name in ('reference','optimized'):
 a=np.array([r[name]['wall_s']*1000 for r in rows]);summary[name]=dict(p50=float(np.median(a)),p95=float(np.quantile(a,.95)),p99=float(np.quantile(a,.99)),maximum=float(a.max()))
atomic_json(args.output,dict(rows=rows,summary_ms=summary,exact_all_outputs=True,p95_reduction=1-summary['optimized']['p95']/summary['reference']['p95'],method='four fixed100-case repeats, alternating execution order, no samples excluded; supplements rather than replaces final matrix'))
