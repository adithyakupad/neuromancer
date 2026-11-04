"""Public-record chronological shadow predictors; no neural execution or action choice."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from neuromancer.predictive import FIRModel
from neuromancer.supervisor import Deadline,atomic_json

def run(root,out):
 root=Path(root);out=Path(out);out.mkdir(exist_ok=False);d=Deadline.from_environment();meta=json.loads((root/'provenance.json').read_text());summary=[]
 for n,rep in meta['jobs']:
  folder=root/f'n{n}_r{rep}';initial=json.loads((folder/'initial.json').read_text());record=initial['record'];a=np.load(folder/'initial.npz');prefix=np.load(folder/'prefix.npz');u0=prefix['delivered'];y0=prefix['counts'].reshape(2550,4,5)[:,:,:4].sum(2)/.4;k=np.arange(800,2350);X=np.hstack([u0[k-j] for j in range(10)]);X=np.roll(X,250,axis=0);mu=X.mean(0);scale=np.maximum(X.std(0),1);Z=np.c_[np.ones(len(X)),(X-mu)/scale];Y=y0[k]-np.asarray(record['output_mean']);A=Z.T@Z+len(Z)*.1*np.diag(np.r_[0,np.ones(40)]);shuffled=copy.deepcopy(record);shuffled.update(coef=np.linalg.solve(A,Z.T@Y).tolist(),mean=mu.tolist(),scale=scale.tolist())
  for reg in ('STATIC','LOSS'):
   for arm in ('FIXED','ZERO'):
    data=np.load(folder/f'{reg}_{arm}.npz');u=data['delivered'];y=data['counts'].reshape(3200,4,5)[:,:,:4].sum(2)/.4;h=np.vstack([a['history'],u]);preds={};diagnostics={}
    for name in ('FIXED','RLS','BIAS','SHUFFLED'):
     model=FIRModel(shuffled if name=='SHUFFLED' else record,np.linalg.inv(A) if name=='SHUFFLED' else a['p'],'FIXED' if name=='SHUFFLED' else name);pred=[];snapshots=[]
     for i in range(3200):
      x=h[i:i+10][::-1].ravel();pred.append(model.predict(x));model.update(x,y[i])
      if (i+1)%500==0 or i==3199:
       end=i+1;raw=np.hstack([h[9-j+max(0,end-500):9-j+end] for j in range(10)]);q=raw[:,::4];z=np.c_[np.ones(len(q)),(q-q.mean(0))/np.maximum(q.std(0),1)];sv=np.linalg.svd(z,compute_uv=False);cond=float(sv[0]/sv[-1]) if sv[-1]>0 else None
       snapshots.append(dict(end_bin=end,reduced_rank=int(np.linalg.matrix_rank(z)),reduced_condition=cond,input_variance_pA2=float(u[max(0,end-500):end,0].var()),distinct_doses=int(len(np.unique(u[max(0,end-500):end,0]))),ramp_transitions=int(np.count_nonzero(np.diff(u[max(0,end-500):end,0]))),smallest_information_eigenvalue=float(np.linalg.eigvalsh(np.linalg.inv(model.p)).min()),coefficient_change_norm=float(np.linalg.norm(model.theta-np.asarray(model.record['coef'])))))
     pred=np.array(pred);preds[name]=pred;diagnostics[name]=dict(post_mse_hz2=float(((pred[800:]-y[800:])**2).mean()),post_signed_bias_hz=float((pred[800:]-y[800:]).mean()),failure=model.failure,updates=model.updates,windows=snapshots,terminal_theta=model.theta.tolist())
    np.savez_compressed(out/f'n{n}_r{rep}_{reg}_{arm}.npz',observations=y,delivered=u,**preds);summary.append(dict(network=n,replicate=rep,condition=reg,acquired_controller=arm,models=diagnostics,causal_counterfactual_control_claim=False));d.check()
 atomic_json(out/'summary.json',dict(status='COMPLETE',records=summary,shuffled_fit_row_roll=250,permitted_inputs_only=True,no_new_neural_data=True));d.check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('out');a=p.parse_args();run(a.root,a.out)
