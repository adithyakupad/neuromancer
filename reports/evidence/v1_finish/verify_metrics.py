"""Second implementation of M005B raw-count endpoints and whole-network gates."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json

def read(p):return json.loads(Path(p).read_text())
def verify(root,analysis,out):
 root=Path(root);analysis=Path(analysis);d=Deadline.from_environment();meta=read(root/'provenance.json');summary=read(analysis/'summary.json');nets=sorted({n for n,r in meta['jobs']});N=len(nets);assert N in (5,10);rows=list(csv.DictReader((analysis/'trial_metrics.csv').open()));data={};checks=0
 for n,r in meta['jobs']:
  f=root/f'n{n}_r{r}';c=read(f/'initial.json')['calibration'];p=np.load(f/'prefix.npz');u=p['delivered'];counts=p['counts'].reshape(2550,4,5)[:,:,:4].sum((1,2));raw=counts/1.6;b=raw[350:750].mean();h=np.r_[0.,[raw[1000+400*j:1150+400*j].mean()-raw[800+400*j:950+400*j].mean() for j in range(4)]];q=np.arange(0,121,30);slope=q@h/(q@q);ff=1/slope if slope>0 else 0.;noise=(counts[350:750].reshape(8,50).sum(1)/80).std(ddof=1);valid=bool(1<=b<=30 and slope>0 and np.max(abs(q*slope-h))<=.5 and np.min(np.diff(h))>=-.3 and 0<=ff<=120)
  for key,value in dict(baseline_hz=b,target_hz=b+1,noise_hz=noise,slope_hz_per_pA=slope,feedforward_pA=ff).items():np.testing.assert_allclose(c[key],value,rtol=1e-12,atol=1e-12)
  assert c['valid']==valid
  for br in read(f/'trial.json')['branches']:
   a=np.load(f/(br['name']+'.npz'));e=a['counts'].reshape(64,50,4,5)[:,:,:,:4].sum((1,2,3))/80-b-1;delivered=a['delivered'];z=dict(error=e,cal=c,current=delivered,branch=br)
   data[n,r,br['condition'],br['controller']]=z
   row=next(x for x in rows if int(x['network'])==n and int(x['replicate'])==r and x['condition']==br['condition'] and x['controller']==br['controller'])
   for name,(lo,hi) in dict(full=(0,64),pre=(0,16),post=(16,64),late=(48,64),block1=(48,56),block2=(56,64)).items():
    for suffix,val in dict(bias_hz=e[lo:hi].mean(),mae_hz=abs(e[lo:hi]).mean(),iae_hz_s=abs(e[lo:hi]).sum(),exposure_pA_s=delivered[lo*50:hi*50].sum()*.02).items():np.testing.assert_allclose(float(row[name+'_'+suffix]),val,rtol=1e-12,atol=1e-12);checks+=1
  d.check()
 repeats=sorted({r for n,r in meta['jobs']});draws=np.random.Generator(np.random.PCG64(20261105)).integers(N,size=(10000,N))
 def ci(a):return np.quantile(np.asarray(a)[draws].mean(1),[.025,.975])
 def values(reg,kind,func):return np.array([np.mean([func(data[n,r,reg,kind]) for r in repeats]) for n in nets])
 def iae(z,lo=16,hi=64):return abs(z['error'][lo:hi]).sum()
 required=[]
 for hyp,ref,relative,absolute in [('H1a','PI10_5',.10,1.2),('H1b','FIXED-MPC',.05,.6)]:
  a=values('LOSS',ref,iae);b=values('LOSS','RLS-MPC',iae);delta=a-b;ratio=delta/np.maximum(a,.01);g=summary[hyp];np.testing.assert_allclose(g['absolute']['network_values'],delta);np.testing.assert_allclose(g['absolute']['ci95'],ci(delta));np.testing.assert_allclose(g['relative']['network_values'],ratio);passed=bool(delta.mean()>=absolute and ratio.mean()>=relative and ci(delta)[0]>0 and (delta>0).sum()>=(8 if N==10 else 4));assert passed==g['pass_gate'];required.append(passed)
 for reg in ('STATIC','LOSS'):
  qualifications=[];biases=[]
  for n in nets:
   zs=[data[n,r,reg,'RLS-MPC'] for r in repeats];maxmargin=np.mean([data[n,r,'LOSS','MAX']['error'][48:64].mean() for r in repeats]);bs=np.mean([z['error'][48:64].mean() for z in zs]);biases.append(bs)
   ok=all(z['cal']['valid'] and 1<=z['cal']['baseline_hz']<=30 for z in zs) and 2*np.sqrt(np.mean([z['cal']['noise_hz']**2 for z in zs]))<=1 and (reg=='STATIC' or maxmargin>=.2)
   for lo,hi in ((48,64),(48,56),(56,64)):ok=ok and abs(np.mean([z['error'][lo:hi].mean() for z in zs]))<=.2 and np.mean([abs(z['error'][lo:hi]).mean() for z in zs])<=.35
   ok=ok and all(not z['branch']['safe_bins'] and not z['branch']['violations'] and not z['branch']['model_failure'] for z in zs);qualifications.append(bool(ok))
  passed=bool(sum(qualifications)>=(8 if N==10 else 4) and ci(biases)[0]>=-.2 and ci(biases)[1]<=.2);assert passed==summary['H3'][reg+'_RLS-MPC']['pass_gate'];required.append(passed)
  lo=0 if reg=='STATIC' else 16;den=values(reg,'PI10_5',lambda z:z['current'][lo*50:].sum()*.02);num=values(reg,'RLS-MPC',lambda z:z['current'][lo*50:].sum()*.02);passed=bool((den>0).all() and (num/den).mean()<=1.1 and ci(num/den)[1]<=1.15);assert passed==summary['H4'][reg]['pass_gate'];required.append(passed)
  lo,hi=(0,64) if reg=='STATIC' else (0,16);ref=values(reg,'PI10_5',lambda z:iae(z,lo,hi));ada=values(reg,'RLS-MPC',lambda z:iae(z,lo,hi));harm=(ada-ref)/np.maximum(ref,.01);passed=bool(harm.mean()<=.05 and ci(harm)[1]<=.10);assert passed==summary['H5'][reg]['pass_gate'];required.append(passed)
 safety=all(not z['branch']['safe_bins'] and not z['branch']['violations'] and not z['branch']['model_failure'] for z in data.values());assert safety==summary['safety_pass'];required.append(safety);assert all(required)==summary['scientific_pass'];d.check();atomic_json(out,dict(status='PASS',networks=nets,trials=len(meta['jobs']),raw_metric_checks=checks,scientific_pass_independently_reproduced=bool(all(required)),calibration_reconstructed=True,bootstrap_draws=10000,bootstrap_seed=20261105))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('analysis');p.add_argument('out');a=p.parse_args();verify(a.root,a.analysis,a.out)
