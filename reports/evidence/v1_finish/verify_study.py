"""Independent public-count, scalar PI, planner and weighted-equation audit."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from neuromancer.predictive import FIRModel
from neuromancer.research_codec import model_digest
from neuromancer.supervisor import Deadline,atomic_json

def close(a,b):np.testing.assert_allclose(a,b,rtol=2e-8,atol=2e-8,equal_nan=True)
def read(p):return json.loads(Path(p).read_text())

def verify(root,output):
 root=Path(root);output=Path(output);d=Deadline.from_environment();meta=read(root/'provenance.json');totals=dict(trials=0,branches=0,bins=0,model_hashes=0,candidate_scores=0,violations=0,fallback_bins=0);invalid=[]
 for n,rep in meta['jobs']:
  folder=root/f'n{n}_r{rep}';trial=read(folder/'trial.json');assert trial['status']=='complete' and (trial['network'],trial['replicate'])==(n,rep)
  initial=read(folder/'initial.json');c=initial['calibration'];record=initial['record'];arr=dict(np.load(folder/'initial.npz'));prefix=dict(np.load(folder/'prefix.npz'));u0=prefix['delivered'];y0=prefix['counts'].reshape(2550,4,5)[:,:,:4].sum(2)/.4;k=np.arange(800,2350);X=np.hstack([u0[k-j] for j in range(10)]);mu=X.mean(0);scale=np.maximum(X.std(0),1.);ym=y0[k].mean(0);Z=np.c_[np.ones(len(k)),(X-mu)/scale];A0=Z.T@Z+len(k)*.1*np.diag(np.r_[0.,np.ones(40)]);H0=Z.T@(y0[k]-ym);theta0=np.linalg.solve(A0,H0);close(theta0,record['coef']);close(mu,record['mean']);close(scale,record['scale']);close(ym,record['output_mean']);close(np.linalg.inv(A0),arr['p'])
  noise=None
  for branch in trial['branches']:
   data=dict(np.load(folder/(branch['name']+'.npz')));u=data['delivered'];counts=data['counts'];bins=len(u);assert bins==(100 if meta['phase']=='engineering' else 3200)
   assert np.array_equal(data['requested'],u) and (u>=0).all() and (u<=120).all() and (u.sum(1)<=240).all() and (abs(np.diff(np.vstack([arr['history'][-1],u]),axis=0))<=30).all() and not u[:,1::2].any() and np.array_equal(u[:,0],u[:,2])
   times=np.arange(51_000_000,51_000_000+bins*20000,20000);np.testing.assert_array_equal(data['time_us'],np.c_[times,times+20000,times+20000]);assert data['valid'].all() and (data['coverage_us']==20000).all()
   for i in range(bins):
    a,b=data['event_offset'][i:i+2];ts=data['event_time_us'][a:b];channels=data['event_channel'][a:b];assert ((ts>=times[i])&(ts<times[i]+20000)).all();np.testing.assert_array_equal(np.bincount(channels,minlength=20),counts[i])
   if noise is None:noise=branch['noise']
   else:assert noise==branch['noise']
   close(branch['exposure_pA_s'],u.sum()*.02);totals['branches']+=1;totals['bins']+=bins;totals['fallback_bins']+=branch['safe_bins'] if branch['fault'] is None else 0
   kind=branch['controller'];raw=counts.reshape(bins,4,5)[:,:,:4].sum(2)/.4
   if kind.endswith('-MPC'):
    plan_goals={int(np.load(folder/f'{branch["name"]}_plan_{j:02}.npz')['origin_us']):float(np.load(folder/f'{branch["name"]}_plan_{j:02}.npz')['q0']) for j in range(branch['plans'])}
    action_prior=arr['history'][-1,0]
    m=FIRModel(record,arr['p'],kind.split('-')[0]);history=np.vstack([arr['history'],u]);A=A0.copy();H=H0.copy();ab=len(k);hb=ab*theta0[0].copy();dense=0
    for i in range(bins):
     if not branch['model_failure']:
      goal=plan_goals.get(int(times[i]),0. if i==0 or data['frames'][i-1,2] else data['frames'][i-1,1]);low=max(0.,action_prior-30);high=min(120.,action_prior+30);action_prior=min(high,max(low,goal));close(u[i],[action_prior,0,action_prior,0])
     xx=history[i:i+10][::-1].ravel();zz=np.r_[1.,(xx-mu)/scale];prediction=ym+zz@m.theta
     if np.isfinite(data['pre_prediction'][i]).all():close(prediction,data['pre_prediction'][i])
     target_updates=int(data['frames'][i,5]);eligible=target_updates>m.updates if m.kind!='FIXED' else int(data['frames'][i,6])==m.skips
     m.update(xx,raw[i],eligible);assert model_digest(m)==data['state_hashes'][i].tobytes();totals['model_hashes']+=1
     if eligible:
      if m.kind=='RLS':A=.999*A+np.outer(zz,zz);H=.999*H+np.outer(zz,raw[i]-ym)
      elif m.kind=='BIAS':ab=.999*ab+1;hb=.999*hb+raw[i]-ym-zz[1:]@theta0[1:]
     if (i+1)%50==0:
      close(m.theta,data['dense_theta'][dense]);close(m.p,data['dense_p'][dense])
      if m.kind=='RLS':close(np.linalg.solve(A,H),m.theta);close(np.linalg.inv(A),m.p)
      elif m.kind=='BIAS':close(hb/ab,m.theta[0]);close(theta0[1:],m.theta[1:])
      dense+=1
    for second in range(branch['plans']):
     p=dict(np.load(folder/f'{branch["name"]}_plan_{second:02}.npz'));origin=int(p['origin_us']);index=(origin-51_000_000)//20000;close(p['history'],history[index:index+9]);close(p['theta'],theta0 if index==0 else data['dense_theta'][index//50-1])
     q0=np.repeat(np.arange(0,121,5),25);q1=np.tile(np.arange(0,121,5),25);bank=np.empty((625,100));prior=np.full(625,p['history'][-1,0])
     for j in range(100):
      lo=np.maximum(0,prior-30);hi=np.minimum(120,prior+30)
      bad=prior-lo>30;lo[bad]=np.nextafter(lo[bad],prior[bad]);bad=hi-prior>30;hi[bad]=np.nextafter(hi[bad],prior[bad]);prior=np.minimum(hi,np.maximum(lo,q0 if j<50 else q1));bank[:,j]=prior
     B=p['theta'][1:]/scale[:,None];offset=ym+p['theta'][0]-mu@B;gamma=(B.reshape(10,4,4)[:,0,:]+B.reshape(10,4,4)[:,2,:]).mean(1);full=np.c_[np.broadcast_to(p['history'][:,0],(625,9)),bank];means=np.full((625,2),offset.mean())
     for lag in range(10):
      for h in range(2):means[:,h]+=gamma[lag]*full[:,9-lag+h*50:59-lag+h*50].mean(1)
     tracking=((means-c['target_hz'])**2).sum(1);dose=.02*np.sum(.02*(bank/120)**2,axis=1);switch=.01*((q0-p['history'][-1,0])**2+(q1-q0)**2)/120**2;cost=tracking+dose+switch;close(tracking,p['tracking']);close(dose,p['dose']);close(switch,p['switch']);close(cost,p['cost']);exposure=bank.sum(1)*.04;close(exposure,p['exposure']);near=np.flatnonzero(cost<=cost.min()+1e-12);winner=int(near[np.lexsort((q1[near],q0[near],exposure[near]))[0]]);assert winner==int(p['chosen']);totals['candidate_scores']+=625
     if not branch['model_failure'] and branch['fault'] is None:close(u[index:index+50,0],bank[winner,:50])
   else:
    q=0. if kind=='ZERO' else 120. if kind=='MAX' else c['feedforward_pA'];I=0.;err=np.nan;blocked=clipped=False;safe=not c['valid'] and kind not in ('ZERO','MAX');recover=4;samples=[];updates=0;prior=0.
    for i in range(bins):
     desired=0 if safe else q;lo=max(0,prior-30);hi=min(120,prior+30)
     if prior-lo>30:lo=np.nextafter(lo,prior)
     if hi-prior>30:hi=np.nextafter(hi,prior)
     prior=min(hi,max(lo,desired));close(u[i],[prior,0,prior,0])
     if not data['presented'][i]:safe=True;recover=0;samples=[]
     elif not c['valid'] and kind not in ('ZERO','MAX'):safe=True
     elif recover<4:
      recover+=1
      if recover==4:safe=False
     else:
      safe=False;samples.append(float(counts[i].reshape(4,5)[:,:4].sum())/1.6)
      if len(samples)==50:
       err=c['target_hz']-sum(samples)/50;samples=[];blocked=clipped=False
       if kind=='PI10_5':
        proposed=min(120.,max(-120.,I+5*err));candidate=c['feedforward_pA']+10*err+proposed;blocked=(candidate>120 and err>0) or (candidate<0 and err<0)
        if not blocked:I=proposed
        candidate=c['feedforward_pA']+10*err+I;q=min(120.,max(0.,candidate));clipped=candidate!=q
       updates+=1
     close(data['frames'][i],[51_020_000+i*20000,q,I,err,float(blocked),float(clipped),float(safe),updates])
   if branch['model_failure']:invalid.append(dict(network=n,replicate=rep,branch=branch['name'],reason=branch['model_failure']))
   d.check()
  totals['trials']+=1
 atomic_json(output,dict(status='PASS',**totals,invalid_models=invalid,primary_instrument_valid=not invalid and totals['fallback_bins']==0,scientific_outcome_scored=False));d.check()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('output');a=p.parse_args();verify(a.root,a.output)
