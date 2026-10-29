"""Descriptive network-level prediction and bias-only ablation summaries."""
import argparse,json,csv
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json

def run(analysis,out):
 d=Deadline.from_environment();analysis=Path(analysis);records=json.loads((analysis/'model_diagnostics.json').read_text());nets=sorted({r['network'] for r in records});draws=np.random.Generator(np.random.PCG64(20261105)).integers(len(nets),size=(10000,len(nets)));result=[]
 for reg in ('STATIC','LOSS'):
  for kind in ('FIXED-MPC','RLS-MPC','BIAS-MPC'):
   for key in ('own_post_mse','frozen_on_same_inputs_post_mse','prospective_first_second_post_mse','terminal_kernel_scale_proxy'):
    groups=[[r[key] for r in records if r['network']==n and r['condition']==reg and r['controller']==kind] for n in nets];missing=sum(any(v is None for v in g) for g in groups)
    if missing:result.append(dict(condition=reg,controller=kind,metric=key,mean=None,ci95=None,missing_networks=missing));continue
    x=np.array([np.mean(g) for g in groups]);result.append(dict(condition=reg,controller=kind,metric=key,mean=float(x.mean()),ci95=np.quantile(x[draws].mean(1),[.025,.975]).tolist(),network_values=x.tolist(),missing_networks=0))
 atomic_json(out,dict(records=result,uncertainty='repeat-averaged network bootstrap;10000PCG64seed20261105',interpretation='Between-controller prediction errors are descriptive on different closed-loop trajectories. Own-versus-frozen comparison uses the same actual delivered inputs. Kernel scale projection is not an identifiable physical gain estimator.'));d.check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('analysis');p.add_argument('out');a=p.parse_args();run(a.analysis,a.out)
