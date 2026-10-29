"""Prespecified cost/antiwindup/excitation details from all saved arms."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json

def run(root,out):
 root=Path(root);out=Path(out);out.mkdir(exist_ok=False);d=Deadline.from_environment();meta=json.loads((root/'provenance.json').read_text());rows=[];excitation=[];gains=[]
 for n,rep in meta['jobs']:
  folder=root/f'n{n}_r{rep}';trial=json.loads((folder/'trial.json').read_text());prefix=np.load(folder/'prefix.npz')['delivered'];history=np.load(folder/'initial.npz')['history']
  for b in trial['branches']:
   a=np.load(folder/(b['name']+'.npz'));u=a['delivered'];f=a['frames'];key=dict(network=n,replicate=rep,condition=b['condition'],controller=b['controller'],fault=b['fault'] or '');row=key.copy();row.update(total_current_squared_pA2_s=float((u*u).sum()*.02),total_budget_saturation_fraction=float((u.sum(1)==240).mean()),ramp_tick_count=int(np.count_nonzero(np.any(np.diff(np.vstack([history[-1],u]),axis=0)!=0,axis=1))),current_distinct_q=int(len(np.unique(u[:,0]))))
   for j in range(4):
    row[f'channel{j}_control_pA_s']=float(u[:,j].sum()*.02);row[f'channel{j}_calibration_pA_s']=float(prefix[:,j].sum()*.02);row[f'channel{j}_squared_pA2_s']=float((u[:,j]**2).sum()*.02);row[f'channel{j}_max_fraction']=float((u[:,j]==120).mean())
   if not b['controller'].endswith('-MPC'):
    decisions=np.r_[f[0,7]>0,np.diff(f[:,7])>0];row.update(antiwindup_blocked_decisions=int(f[decisions,4].sum()),clipped_decisions=int(f[decisions,5].sum()),integral_initial=0.,integral_final=float(f[-1,2]),integral_min=float(f[:,2].min()),integral_max=float(f[:,2].max()))
   else:row.update(antiwindup_blocked_decisions='',clipped_decisions='',integral_initial='',integral_final='',integral_min='',integral_max='')
   rows.append(row);h=np.vstack([history,u])
   for end in (500,1000,1600,2400,3200):
    x=np.column_stack([h[9-j+end-500:9-j+end,0] for j in range(10)]);z=np.c_[np.ones(500),(x-x.mean(0))/np.maximum(x.std(0),1.)];sv=np.linalg.svd(z,compute_uv=False);excitation.append(dict(**key,end_bin=end,reduced_rank=int(np.linalg.matrix_rank(z)),reduced_condition=float(sv[0]/sv[-1]) if sv[-1]>0 else None,smallest_design_information_eigenvalue=float(np.linalg.eigvalsh(z.T@z).min()),q_variance_pA2=float(u[end-500:end,0].var()),distinct_q=int(len(np.unique(u[end-500:end,0])))))
   gains.append(dict(**key,absolute_start_us=51_000_000,bin_us=20000,seconds=64,evaluator_only_gain_by_second=[.6 if b['condition']=='LOSS' and t>=16 else 1. for t in range(64)],provenance='Reconstructed from frozen condition and acquisition source gain assignment; not a separately sampled hardware measurement.'))
  d.check()
 with (out/'cost_and_antiwindup.csv').open('w') as stream:
  w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 atomic_json(out/'excitation.json',excitation);atomic_json(out/'evaluator_gain_schedule.json',gains);d.check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('out');a=p.parse_args();run(a.root,a.out)
