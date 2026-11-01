"""M007 independent raw-count audit; never invokes a neural simulator."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json
R=Path('reports/evidence/m007');B=Path('reports/evidence/v1_finish/m005b');D=Deadline.from_environment()
def read(p):return json.loads(Path(p).read_text())
def interval(x):
 x=np.asarray(x,float);draw=np.random.Generator(np.random.PCG64(20261105)).integers(0,len(x),(10000,len(x)));return dict(mean=float(x.mean()),ci95=np.quantile(x[draw].mean(1),[.025,.975]).tolist(),network_values=x.tolist())
def main():
 D.check();preservation={};total=0
 for file,key in [('preservation.json','historical_sha256'),('release_manifest.json','sha256')]:
  m=read(Path('reports/evidence/v1_finish')/file)[key];bad=[]
  for i,(p,h) in enumerate(m.items()):
   if i%200==0:D.check()
   if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:bad.append(p)
  assert not bad;preservation[file]=dict(files=len(m),mismatches=bad);total+=len(m)
 rows=[];counts_total=0;events_total=0;safety={};calibration={}
 for phase,jobs in [('primary',[(n,r) for n in range(10) for r in (47,48)]),('faults',[(n,49) for n in range(3)])]:
  root=B/phase;assert set(map(tuple,read(root/'provenance.json')['jobs']))==set(jobs);assert len(list(root.glob('n*_r*/trial.json')))==len(jobs)
  for n,r in jobs:
   folder=root/f'n{n}_r{r}';trial=read(folder/'trial.json');assert trial['status']=='complete' and (n,r)==(trial['network'],trial['replicate']);prefix=np.load(folder/'prefix.npz');pc=prefix['counts'].reshape(2550,4,5)[:,:,:4].sum((1,2));base=pc[350:750].sum()/(80*8);target=base+1;noise=(pc[350:750].reshape(8,50).sum(1)/80).std(ddof=1);c=read(folder/'initial.json')['calibration'];np.testing.assert_allclose([base,target,noise],[c['baseline_hz'],c['target_hz'],c['noise_hz']],rtol=0,atol=1e-12);calibration[n,r]=c
   expected={(reg,k,None) for reg in ('STATIC','LOSS') for k in ('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO')}|{('LOSS','MAX',None)} if phase=='primary' else {(reg,k,fault) for reg in ('STATIC','LOSS') for k in ('PI10_5','RLS-MPC') for fault in ('DELAY','DROP')}
   assert {(x['condition'],x['controller'],x['fault']) for x in trial['branches']}==expected
   for branch in trial['branches']:
    a=np.load(folder/(branch['name']+'.npz'));u=a['delivered'];cnt=a['counts'];assert cnt.shape==(3200,20) and np.all(cnt>=0);rate=cnt.reshape(64,50,4,5)[:,:,:,:4].sum((1,2,3))/80.;err=rate-target;t=np.arange(51_000_000,115_000_000,20000);np.testing.assert_array_equal(a['time_us'],np.c_[t,t+20000,t+20000]);assert a['valid'].all() and (a['coverage_us']==20000).all();np.testing.assert_array_equal(a['requested'],u)
    violations=int((~np.isfinite(u)).sum()+(u<0).sum()+(u>120).sum()+(u.sum(1)>240).sum()+(abs(np.diff(np.vstack([prefix['delivered'][-1],u]),axis=0))>30).sum());assert violations==branch['violations']==0;assert (u[:,1::2]==0).all() and (u[:,0]==u[:,2]).all()
    et=a['event_time_us'];ch=a['event_channel'];bi=(et-51_000_000)//20000;assert ((bi>=0)&(bi<3200)&(ch>=0)&(ch<20)).all();np.testing.assert_array_equal(np.bincount(bi*20+ch,minlength=64000).reshape(3200,20),cnt);np.testing.assert_array_equal(np.diff(a['event_offset']),cnt.sum(1));events_total+=len(et);counts_total+=3200
    safe=int(a['frames'][:,2 if branch['controller'].endswith('-MPC') else 6].sum());assert safe==branch['safe_bins'];assert not branch['model_failure'];assert a['presented'].all() if phase=='primary' else np.array_equal(np.flatnonzero(~a['presented']),np.arange(1200,1250))
    row=dict(phase=phase,network=n,replicate=r,condition=branch['condition'],controller=branch['controller'],fault=branch['fault'] or '',target_hz=target,noise_hz=noise,valid_calibration=c['valid'],violations=violations,safe_bins=safe,calibration_exposure_pA_s=float(prefix['delivered'].sum()*.02))
    for name,(lo,hi) in dict(full=(0,64),pre=(0,16),post=(16,64),late=(48,64),b1=(48,56),b2=(56,64)).items():row[name+'_iae']=float(abs(err[lo:hi]).sum());row[name+'_bias']=float(err[lo:hi].mean());row[name+'_mae']=float(abs(err[lo:hi]).mean());row[name+'_dose']=float(u[lo*50:hi*50].sum()*.02)
    rows.append(row)
   D.check()
  terminal=read(root/'supervision/terminal.json');closure=read(B/(phase+'_closure.json'));assert terminal['cleanup_verified'] and not terminal['post_deadline_cleanup'] and terminal['status']=='COMPLETED';assert all(w['state']=='REAPED' and w['parent_reaped'] for w in terminal['workers']);assert closure['status']=='COMPLETE' and closure['finished_ns']<closure['deadline']['end_ns'];samples=[json.loads(line) for line in (B/(phase+'_resource.jsonl')).read_text().splitlines()];assert all(max(s['rss_bytes'].values(),default=0)<2*2**30 and s['completed_peak_rss_bytes']<2*2**30 and s['aggregate_rss_bytes']<=6*2**30 and s['mission_allocated_bytes']<=750*2**20 and s['combined_allocated_bytes']<=int(1.2*2**30) for s in samples);safety[phase]=dict(trials=len(jobs),branches=sum(x['phase']==phase for x in rows),safe_bins=sorted({x['safe_bins'] for x in rows if x['phase']==phase}),violations=0,aborts=0,resource_samples=len(samples),cleanup=True)
 primary=[r for r in rows if r['phase']=='primary'];nets=range(10)
 def values(reg,kind,key):return np.array([np.mean([r[key] for r in primary if r['network']==n and r['condition']==reg and r['controller']==kind]) for n in nets])
 models={kind:interval(values('LOSS',kind,'post_iae')) for kind in ('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO')};comparisons={}
 for name,ref,rel,ab in [('H1a','PI10_5',.1,1.2),('H1b','FIXED-MPC',.05,.6)]:
  base=values('LOSS',ref,'post_iae');ada=values('LOSS','RLS-MPC','post_iae');delta=base-ada;effect=interval(delta);ratio=interval(delta/np.maximum(base,.01));positive=int((delta>0).sum());passed=effect['mean']>=ab and ratio['mean']>=rel and effect['ci95'][0]>0 and positive>=8;comparisons[name]=dict(absolute=effect,relative=ratio,positive=positive,pass_gate=bool(passed),floor_activations=int((base<.01).sum()))
 guards={}
 for reg in ('STATIC','LOSS'):
  qualified=[]
  for n in nets:
   rr=[r for r in primary if r['network']==n and r['condition']==reg and r['controller']=='RLS-MPC'];mr=[r for r in primary if r['network']==n and r['controller']=='MAX'];ok=all(r['valid_calibration'] and 1<=r['target_hz']-1<=30 for r in rr) and 2*np.sqrt(np.mean([r['noise_hz']**2 for r in rr]))<=1 and (reg=='STATIC' or np.mean([r['late_bias'] for r in mr])>=.2)
   ok=ok and all(abs(np.mean([r[w+'_bias'] for r in rr]))<=.2 and np.mean([r[w+'_mae'] for r in rr])<=.35 for w in ('late','b1','b2'));qualified.append(bool(ok))
  ci=interval(values(reg,'RLS-MPC','late_bias'));h3=sum(qualified)>=8 and ci['ci95'][0]>=-.2 and ci['ci95'][1]<=.2;window='full' if reg=='STATIC' else 'post';ratio=interval(values(reg,'RLS-MPC',window+'_dose')/values(reg,'PI10_5',window+'_dose'));h4=ratio['mean']<=1.1 and ratio['ci95'][1]<=1.15;window='full' if reg=='STATIC' else 'pre';ref=values(reg,'PI10_5',window+'_iae');harm=interval((values(reg,'RLS-MPC',window+'_iae')-ref)/np.maximum(ref,.01));h5=harm['mean']<=.05 and harm['ci95'][1]<=.1;guards[reg]=dict(H3=bool(h3),qualified=sum(qualified),bias=ci,H4=bool(h4),dose_ratio=ratio,H5=bool(h5),harm=harm)
 old=read(B/'analysis_primary/summary.json')
 for k,model in models.items():np.testing.assert_allclose(model['network_values'],old['models']['LOSS_'+k]['post_iae_hz_s']['network_values'],rtol=0,atol=1e-12)
 for k,x in comparisons.items():assert x['pass_gate']==old[k]['pass_gate'];np.testing.assert_allclose(x['absolute']['ci95'],old[k]['absolute']['ci95'],rtol=0,atol=1e-12);np.testing.assert_allclose(x['relative']['ci95'],old[k]['relative']['ci95'],rtol=0,atol=1e-12)
 for reg,g in guards.items():assert g['H3']==old['H3'][reg+'_RLS-MPC']['pass_gate'] and g['H4']==old['H4'][reg]['pass_gate'] and g['H5']==old['H5'][reg]['pass_gate']
 assert not old['scientific_pass'] and not comparisons['H1a']['pass_gate'] and comparisons['H1b']['pass_gate'];assert not (B/'validation').exists();D.check()
 with (R/'independent_trials.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 atomic_json(R/'independent_results.json',dict(status='PASS',preservation=preservation,models=models,comparisons=comparisons,guards=guards,safety=safety,observed_bins=counts_total,observed_events=events_total,adaptive_superiority='FAIL',validation='NOT EXECUTED',locked='NOT EXECUTED'));D.check()
if __name__=='__main__':main()
