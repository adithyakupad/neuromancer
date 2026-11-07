"""Independent raw-unit predictor/update/planner/receipt and PI replay audit."""
import hashlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json
from neuromancer.control import ControlCalibration
from neuromancer.predictive import PIReference,public_step
from neuromancer.observation import Observation
from neuromancer.substrate import Receipt
R=Path(__file__).resolve().parent;S=R/'smoke'
def close(a,b):np.testing.assert_allclose(a,b,rtol=1e-9,atol=1e-9,equal_nan=True)
def read(p):return json.loads(p.read_text())
def raw(d):return d['counts'].reshape(-1,4,5)[:,:,:4].sum(2)/.4
def feature(history):return history[::-1].ravel()
def timing(x):
 x=np.array(x)/1e6
 return dict(samples=len(x),p50_ms=float(np.quantile(x,.5)),p95_ms=float(np.quantile(x,.95)),p99_ms=float(np.quantile(x,.99)),max_ms=float(x.max()))
def main():
 dline=Deadline.from_environment();dline.check();summary=read(S/'summary.json');assert summary['status']=='PASS' and summary['peak_rss_bytes']<2*1024**3
 record=read(S/'initial.json')['record'];initial=dict(np.load(S/'initial.npz'));pref=dict(np.load(S/'prefix.npz'));u=pref['delivered'];k=np.arange(800,2350);x=np.hstack([u[k-j] for j in range(10)]);mean=x.mean(0);scale=np.maximum(x.std(0),1.);ym=raw(pref)[k].mean(0);z=np.c_[np.ones(len(k)),(x-mean)/scale];a0=z.T@z+len(k)*.1*np.diag(np.r_[0.,np.ones(40)]);h0=z.T@(raw(pref)[k]-ym);coef=np.linalg.solve(a0,h0)
 close(record['coef'],coef);close(record['mean'],mean);close(record['scale'],scale);close(record['output_mean'],ym);close(initial['p'],np.linalg.inv(a0));checks=0;plans=0;all_command=[];all_update=[];all_planner=[];all_complete=[];exposures={}
 for kind in ('FIXED','RLS','BIAS','RLS_REPLAY'):
  data=dict(np.load(S/f'{kind}.npz'));y=raw(data);history=np.vstack([initial['history'],data['delivered']]);theta=coef.copy();a=a0.copy();h=h0.copy();ab=len(k);hb=ab*coef[0].copy();previous=initial['history'][-1]
  assert data['counts'].shape==(100,20) and data['time_us'][0,0]==51_000_000 and data['time_us'][-1,1]==53_000_000 and data['valid'].all() and (data['coverage_us']==20000).all()
  close(data['commands'],data['delivered']);assert (data['delivered']>=0).all() and (data['delivered']<=120).all() and (data['delivered'].sum(1)<=240).all() and (abs(np.diff(np.vstack([previous,data['delivered']]),axis=0))<=30).all()
  for i in range(100):
   # Reconstruct observation channels directly from saved events.
   lo,hi=data['event_offset'][i:i+2];channels=data['event_channel'][lo:hi];times=data['event_time_us'][lo:hi];assert ((times>=data['time_us'][i,0])&(times<data['time_us'][i,1])).all();np.testing.assert_array_equal(np.bincount(channels,minlength=20),data['counts'][i])
   xx=feature(history[i:i+10]);zz=np.r_[1.,(xx-mean)/scale];close(xx,data['features'][i]);close(ym+zz@theta,data['pre_prediction'][i])
   if kind.startswith('RLS'):
    a=.999*a+np.outer(zz,zz);h=.999*h+np.outer(zz,y[i]-ym);theta=np.linalg.solve(a,h);close(np.linalg.inv(a),data['p_after'][i])
   elif kind=='BIAS':ab=.999*ab+1;hb=.999*hb+y[i]-ym-zz[1:]@coef[1:];theta[0]=hb/ab;close(data['bias_p'][i],1/ab)
   close(theta,data['theta_after'][i]);checks+=1
  for j in range(2):
   dline.check();p=dict(np.load(S/f'{kind}_plan{j}.npz'));plans+=1;bank=p['bank'];assert bank.shape==(625,100) and (bank>=0).all() and (bank<=120).all() and (abs(np.diff(np.c_[p['history'][-1,0]*np.ones(625),bank],axis=1))<=30).all()
   weights=p['theta'][1:]/scale[:,None];offset=ym+p['theta'][0]-mean@weights;cost=[];exposure=[]
   for candidate in range(625):
    full=np.zeros((109,4));full[:9]=p['history'];full[9:,::2]=bank[candidate,:,None];pred=np.tile(offset,(100,1))
    for lag in range(10):pred+=full[9-lag:109-lag]@weights[lag*4:lag*4+4]
    close(pred,p['predictions'][candidate]);means=pred.reshape(2,50,4).mean((1,2));q0=candidate//25*5.;q1=candidate%25*5.;tracking=sum((means-read(S/'initial.json')['calibration']['target_hz'])**2);dose=.02*np.sum(.02*(bank[candidate]/120)**2);switch=.01*((q0-p['history'][-1,0])**2+(q1-q0)**2)/120**2;cost.append(tracking+dose+switch);exposure.append(2*.02*bank[candidate].sum())
   close(cost,p['cost']);close(exposure,p['exposure']);near=np.flatnonzero(np.array(cost)<=min(cost)+1e-12);winner=min(near,key=lambda i:(exposure[i],i//25,i%25));assert winner==p['chosen'];close(data['delivered'][j*50:(j+1)*50,0],bank[winner,:50]);all_planner.append(int(p['elapsed_ns']))
  events=read(S/f'{kind}_events.json');assert all(not e['safe'] and e['failure'] is None and e['recover']==4 and e['stop_us']==51_020_000+i*20000 for i,e in enumerate(events))
  assert events[-1]['updates']==(0 if kind=='FIXED' else 100) and events[-1]['skips']==0
  all_command.extend(data['command_ns']);all_update.extend(data['update_ns']);all_complete.extend(data['command_ns'][[0,50]]+np.array([0,data['update_ns'][49]]));exposures[kind]=float(data['delivered'].sum()*.02)
 # Exact historical64s normal-path PI replay through the same public_step adapter.
 old=Path('reports/evidence/m005a_7/trials/n0_r45');cal=ControlCalibration(**read(old/'calibration.json'));data=dict(np.load(old/'LOSS_PI10_5.npz'));pi=PIReference(cal,'pi-public-replay',np.zeros(4));states=[]
 class Port:
  time_us=51_000_000
  def advance(self,c,stop):
   i=(self.time_us-51_000_000)//20000;np.testing.assert_array_equal(c.current_pA,data['delivered'][i]);o=Observation('pi-public-replay',*map(int,data['time_us'][i]),tuple(map(int,data['counts'][i])),(0.,)*20,tuple(map(int,data['coverage_us'][i])),tuple(map(bool,data['valid'][i])),(),(),(0.,)*4,(0.,)*4,True);self.time_us=stop;r=Receipt(c.trial_id,c.command_id,c.start_us,c.start_us,stop,c.current_pA,c.current_pA,'delivered','');return SimpleNamespace(observation=o,receipt=r)
 port=Port()
 for i in range(3200):
  if i%50==0:states.append(pi.policy.record())
  public_step(port,pi)
 np.testing.assert_array_equal(states,data['decisions']);np.testing.assert_array_equal(pi.policy.record(),data['terminal'])
 # Synthetic latency stream, no neural scientific data, no efficacy metrics.
 sys.path.insert(0,str(Path('tests').resolve()));from test_predictive import fixture,observation,receipt
 from neuromancer.predictive import PredictiveController
 init,*_=fixture();syn_command=[];syn_update=[];syn_planner=[];syn_complete=[]
 for kind in ('FIXED','RLS','BIAS'):
  c=PredictiveController(init,kind)
  for tick in range(1000):
   command=c.command(c.time_us);c.accept(observation(c.time_us,10.),receipt(command),c.time_us+20000)
  assert c.failure is None and not c.safe
  syn_command.extend(c.command_ns);syn_update.extend(c.update_ns);syn_planner.extend(p['elapsed_ns'] for p in c.plans);syn_complete.extend(c.command_ns[i]+(c.update_ns[i-1] if i else 0) for i in range(0,1000,50))
 for path,h in read(R/'preservation.json')['historical_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
 result=dict(status='PASS',independent_updates=checks,independent_plans=plans,candidate_costs=plans*625,sector_bin_predictions=plans*625*100*4,pi_replay_bins=3200,pi_replay_seconds=64,pi_no_new_neural_acquisition=True,smoke_exposure_pA_s=exposures,smoke=dict(command=timing(all_command),update=timing(all_update),planner=timing(all_planner),complete_decision=timing(all_complete)),synthetic=dict(command=timing(syn_command),update=timing(syn_update),planner=timing(syn_planner),complete_decision=timing(syn_complete)),deadline_misses=0,base_fallbacks=0,scientific_endpoints_calculated=False)
 assert max(all_planner+syn_planner)<250_000_000 and max(syn_command[::50])<250_000_000
 atomic_json(R/'verification.json',result);dline.check();print(json.dumps(result))
if __name__=='__main__':main()
