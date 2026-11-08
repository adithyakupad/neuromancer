"""Independent event counts, scalar PI, continuity, endpoints and gate auditor."""
import csv,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent;RAW=R/'trials';A=R/'analysis'
def read(p):return json.loads(Path(p).read_text())
def close(a,b):np.testing.assert_allclose(a,b,rtol=1e-11,atol=2e-11,equal_nan=True)
def load():
 spec=importlib.util.spec_from_file_location('original_independent',Path('reports/evidence/m005a/verify.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
WINDOWS={'pre':(8,16),'immediate':(16,20),'original_late':(20,32),'middle':(32,48),'block1':(48,56),'block2':(56,64),'late':(48,64),'full':(0,64)}

def segment(full,part,start,stop,decision_start=None):
 for key in ('counts','rates','sector','delivered','requested','time_us','valid','coverage_us'):close(part[key],full[key][start:stop])
 begin,end=full['event_offset'][start],full['event_offset'][stop]
 np.testing.assert_array_equal(part['event_offset'],full['event_offset'][start:stop+1]-begin)
 for key in ('event_time_us','event_channel'):np.testing.assert_array_equal(part[key],full[key][begin:end])
 if decision_start is not None:
  close(part['intent'],full['intent'][start:stop]);close(part['decisions'],full['decisions'][decision_start:decision_start+16]);close(part['terminal'],full['decisions'][decision_start+16])

def policy(data,y,c,name):
 safe=not c['valid'] and name!='MAX';q=120. if name=='MAX' else c['feedforward_pA'];I=0.;err=np.nan;blocked=clipped=False;previous=np.zeros(4)
 for sec in range(64):
  close(data['decisions'][sec],[51e6+sec*1e6,q,I,err,float(blocked),float(clipped),float(safe),0 if safe else sec])
  desired=np.zeros(4) if safe else np.array([q,0,q,0])
  for tick in range(sec*50,(sec+1)*50):
   close(data['intent'][tick],desired);previous=np.clip(desired,np.maximum(0,previous-30),np.minimum(120,previous+30));close(data['delivered'][tick],previous)
  if safe:continue
  # Reconstruct the actual chronological1s accumulation independently,
  # preserving IEEE operation order for clipping/anti-windup boundary flags.
  observed=sum(sum(int(data['counts'][tick,ch]) for ch in range(20) if ch%5!=4)/1.6 for tick in range(sec*50,(sec+1)*50))/50
  err=c['target_hz']-observed;blocked=clipped=False
  if name=='PI10_5':
   proposed=min(120.,max(-120.,I+5*err));candidate=c['feedforward_pA']+10*err+proposed;blocked=(candidate>120 and err>0) or (candidate<0 and err<0)
   if not blocked:I=proposed
   candidate=c['feedforward_pA']+10*err+I;q=min(120.,max(0.,candidate));clipped=candidate!=q
 close(data['terminal'],[115e6,q,I,err,float(blocked),float(clipped),float(safe),0 if safe else 64])

def main():
 Deadline.from_environment().check();began=time.perf_counter();v=load();plan=read(R/'plan.json');meta=read(RAW/'provenance.json');closure=read(R/'acquisition_closure.json');terminal=read(RAW/'supervision/terminal.json')
 assert closure['status']=='COMPLETE' and closure['returncode']==0 and closure['reason'] is None and closure['elapsed_s']<=6600
 assert terminal['status']=='COMPLETED' and terminal['cleanup_verified'] and terminal['finished_ns']<terminal['work_cutoff_ns']<terminal['deadline_ns']
 assert closure['deadline_ns']-closure['started_ns']==6600*10**9 and closure['deadline_ns']==meta['deadline_monotonic_ns']==terminal['deadline_ns'] and closure['clock_id']==terminal['deadline_clock_id']==meta['deadline_clock_id']
 assert subprocess.check_output(['git','show',meta['head']+':reports/evidence/m005a_7/plan.json'])==(R/'plan.json').read_bytes()
 assert subprocess.check_output(['git','show',meta['head']+':docs/research/010_M005A_7_EXTENDED_RECOVERY_PROTOCOL.md'])==Path('docs/research/010_M005A_7_EXTENDED_RECOVERY_PROTOCOL.md').read_bytes()
 assert meta['selection_revision']==plan['selection_revision']
 assert meta['branch_bank']==plan['branches'] and meta['replicates']==[45,46] and meta['horizon_s']==64
 assert len(terminal['workers'])==20;intervals=[]
 for w,pair in zip(terminal['workers'],plan['pairs']):
  assert w['terminal']=='COMPLETED' and w['parent_reaped'] and w['returncode']==0 and w['command'][3:5]==list(map(str,pair)) and w['command'][-1]==str(terminal['deadline_ns'])
  ev=w['events'];assert [e['state'] for e in ev]==['CREATED','RUNNING','REAPED'];assert [e['monotonic_ns'] for e in ev]==sorted(e['monotonic_ns'] for e in ev);intervals.extend([(ev[1]['monotonic_ns'],1),(ev[2]['monotonic_ns'],-1)])
  try:os.killpg(w['pgid'],0)
  except ProcessLookupError:pass
  else:raise AssertionError('Worker group remains')
 count=peak=0
 for _,change in sorted(intervals):count+=change;peak=max(peak,count)
 assert count==0 and peak<=3
 for p,h in read(R/'preservation.json')['historical_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
 for p,h in meta['source_hashes'].items():assert hashlib.sha256(Path('src',p).read_bytes()).hexdigest()==h==hashlib.sha256(subprocess.check_output(['git','show',meta['head']+':src/'+p])).hexdigest()
 assert hashlib.sha256(Path('docs/research/010_M005A_7_EXTENDED_RECOVERY_PROTOCOL.md').read_bytes()).hexdigest()==meta['protocol_sha256']
 assert hashlib.sha256(Path('reports/evidence/m005a_3/tuning_analysis/selection.json').read_bytes()).hexdigest()==plan['selection_sha256']==meta['selection_sha256']
 metrics=list(csv.DictReader((A/'metrics.csv').open()));moving=list(csv.DictReader((A/'moving8.csv').open()));traces=list(csv.DictReader((A/'traces.csv').open()));rec=list(csv.DictReader((A/'recovery.csv').open()));gates=list(csv.DictReader((A/'network_qualification.csv').open()));summary=read(A/'summary.json')
 mi={(int(x['network']),int(x['replicate']),x['condition'],x['controller'],x['window']):x for x in metrics};ti={(int(x['network']),int(x['replicate']),x['condition'],x['controller'],int(x['second'])):x for x in traces};movi={(int(x['network']),int(x['replicate']),x['condition'],x['controller'],int(x['end_second'])):x for x in moving}
 all_scores={};trial_cal={};fallbacks=violations=0;segments=0;pair_set=[]
 for folder in sorted(RAW.glob('n*_r*')):
  m=read(folder/'trial.json');n,k=m['network_id'],m['replicate_id'];pair_set.append((n,k));c=m['calibration'];trial_cal[n,k]=c
  assert m['status']=='complete' and m['horizon_s']==64 and m['peak_rss_bytes']<2*1024**3 and m['engine']['config']['dt_us']==100 and m['engine']['config']['trial_id']==f'm005a7-n{n}-r{k}'
  assert [(b['condition'],b['controller']) for b in m['branches']]==[tuple(x) for x in plan['branches']]
  from neuromancer._brian import realization,innovations,digest
  from neuromancer.substrate import Config
  cfg=Config(network_id=n,replicate_id=k);params=realization(cfg);assert {key:digest(value) for key,value in params.items()}==m['engine']['metadata']['parameter_hashes'];assert not np.intersect1d(params['recording'],params['stimulation']).size
  old=read(f'reports/evidence/m005a/results/tune/n{n}_r40/trial.json');assert old['engine']['metadata']['parameter_hashes']==m['engine']['metadata']['parameter_hashes']
  pref,base=v.inspect_public(folder/'prefix.npz',0,2550);v.calibration(pref,base,c)
  for j in range(3):segment(pref,dict(np.load(folder/f'prefix_progress_{j}.npz')),j*800,(j+1)*800);segments+=1
  cache={};noise=None
  for b in m['branches']:
   cond,name=b['condition'],b['controller'];d,_=v.inspect_public(folder/f'{cond}_{name}.npz',51_000_000,3200,pref['rates'][-1]);cache[cond,name]=d
   # Independently sum raw E-channel counts by second; no producer/gate module.
   assert d['event_offset'][0]==0 and d['event_offset'][-1]==len(d['event_time_us'])==len(d['event_channel']) and (np.diff(d['event_offset'])>=0).all()
   y=np.array([sum(int(d['counts'][t,ch]) for t in range(s*50,(s+1)*50) for ch in range(20) if ch%5!=4)/80 for s in range(64)]);e=y-c['target_hz'];policy(d,y,c,name)
   assert b['audit']['violations']==0;violations+=b['audit']['violations'];fb=int(d['decisions'][:,6].sum());fallbacks+=fb
   assert len(b['noise'])==115
   if noise is None:
    noise=b['noise']
    for block in (0,50,51,66,67,98,114):
     eff,fine=innovations(cfg,block);assert noise[str(block)]==dict(fine=fine,effective=digest(eff))
   else:assert b['noise']==noise
   close(b['audit']['exposure_pA_s'],d['delivered'].sum()*.02)
   for end in (16,32,48):segment(d,dict(np.load(folder/f'{cond}_{name}_progress_{end}.npz')),(end-16)*50,end*50,end-16);segments+=1
   for window,(lo,hi) in WINDOWS.items():
    bias=float(e[lo:hi].mean());mae=float(abs(e[lo:hi]).mean());all_scores[n,k,cond,name,window]=(bias,mae,float(y[lo:hi].mean()),e,fb)
    row=mi[n,k,cond,name,window];sub=d['delivered'][lo*50:hi*50];close([float(row[x]) for x in ('bias_hz','mae_hz','rate_hz','total_mean_pA','window_exposure_pA_s','total_charge_pC')],[bias,mae,y[lo:hi].mean(),sub.sum(1).mean(),sub.sum()*.02,(d['delivered'].sum()+pref['delivered'].sum())*.02*50]);close(float(row['dose_max_fraction']),(sub[:,0]==120).mean());close(float(row['dose_zero_fraction']),(sub[:,0]==0).mean());close(float(row['decision_clip_fraction']),d['decisions'][lo:hi,5].mean());close(float(row['blocked_fraction']),d['decisions'][lo:hi,4].mean());close(float(row['dose_mean_pA']),sub[:,0].mean());close(float(row['window_current_squared_pA2_s']),(sub*sub).sum()*.02);close(float(row['rmse_hz']),np.sqrt(np.mean(e[lo:hi]**2)));close(float(row['terminal_integral_pA']),d['terminal'][2]);assert int(row['fallbacks'])==fb and int(row['violations'])==b['audit']['violations']
   for s in range(64):
    row=ti[n,k,cond,name,s];close([float(row[x]) for x in ('rate_hz','error_hz','q_pA','integral_pA','total_delivered_pA')],[y[s],e[s],d['decisions'][s,1],d['decisions'][s,2],d['delivered'][s*50:(s+1)*50].sum()/50])
   for end in range(8,65):
    row=movi[n,k,cond,name,end];assert int(row['start_second'])==end-8
    close([float(row['bias_hz']),float(row['mae_hz'])],[e[end-8:end].mean(),abs(e[end-8:end]).mean()])
   record=next(x for x in rec if (int(x['network']),int(x['replicate']),x['condition'],x['controller'])==(n,k,cond,name));hits=[i for i in range(16,62) if max(abs(e[i:i+3]))<=.35];possible=[]
   for end in range(32,65):
    good=all(abs(e[z-16:z-8].mean())<=.2 and abs(e[z-16:z-8]).mean()<=.35 and abs(e[z-8:z].mean())<=.2 and abs(e[z-8:z]).mean()<=.35 for z in range(end,65))
    if good:possible.append(end)
   assert (record['settling_censored']=='True')==(not possible) and int(record['observed_post_loss_s'])==48 and int(record['crossings'])==int(np.sum(e[16:-1]*e[17:]<0))
   assert record['first_recovery_endpoint_s']==(str(hits[0]+1-16) if hits else '') and record['recovery_confirmation_s']==(str(hits[0]+3-16) if hits else '') and record['settling_delay_s']==(str(possible[0]-16) if possible else '')
  for name in ('PI10_5','FIXED'):
   a,b=cache['STATIC',name],cache['LOSS',name]
   for field in ('counts','rates','sector'):close(a[field][:800],b[field][:800])
   for field in ('delivered','intent'):close(a[field][:850],b[field][:850])
   close(a['decisions'][:17],b['decisions'][:17])
   if name=='FIXED':close(a['delivered'],b['delivered'])
 assert set(pair_set)=={tuple(x) for x in plan['pairs']} and len(pair_set)==20 and len(metrics)==800 and len(traces)==6400 and len(moving)==5700 and segments==360
 def boot(vals):
  x=np.array(vals);g=np.random.Generator(np.random.PCG64(20261025));return np.percentile(x[g.integers(0,10,(10000,10))].mean(1),[2.5,97.5])
 for cond in ('STATIC','LOSS'):
  qualified=0;biases=[]
  for n in range(10):
   cs=[trial_cal[n,k] for k in (45,46)];valid=all(c['valid'] and 1<=c['baseline_hz']<=30 for c in cs);noise=np.sqrt(np.mean([c['noise_hz']**2 for c in cs]));margin=np.mean([all_scores[n,k,'LOSS','MAX','late'][0] for k in (45,46)]);bs=[];ms=[]
   for window in ('late','block1','block2'):
    bs.append(float(np.mean([all_scores[n,k,cond,'PI10_5',window][0] for k in (45,46)])));ms.append(float(np.mean([all_scores[n,k,cond,'PI10_5',window][1] for k in (45,46)])))
   components=dict(calibration=valid,noise=1>=2*noise,headroom=True if cond=='STATIC' else margin>=.2,bias=abs(bs[0])<=.2,block_bias=abs(bs[1])<=.2 and abs(bs[2])<=.2,mae=ms[0]<=.35,block_mae=ms[1]<=.35 and ms[2]<=.35,valid=all(all_scores[n,k,c,name,'full'][4]==0 for k in (45,46) for c,name in plan['branches']))
   row=next(x for x in gates if int(x['network'])==n and x['condition']==cond)
   for key,value in components.items():assert (row[key]=='True')==value
   assert (row['qualified']=='True')==all(components.values());qualified+=all(components.values());biases.append(bs[0]);close(float(row['bias_hz']),bs[0]);close(float(row['mae_hz']),ms[0]);close(float(row['max_target_margin_hz']),margin)
  ci=boot(biases);passed=bool(qualified>=8 and ci[0]>=-.2 and ci[1]<=.2);close(summary['regimes'][cond]['bias_ci_hz'],ci);assert summary['regimes'][cond]['qualified']==qualified and summary['regimes'][cond]['pass_gate']==passed
 assert summary['fallbacks']==fallbacks and summary['violations']==violations
 assert summary['scientific_pass']==bool(summary['regimes']['STATIC']['pass_gate'] and summary['regimes']['LOSS']['pass_gate'] and fallbacks==0 and violations==0)
 # Every model/window interval and PI-vs-FIXED contrast uses network means.
 for cond,name in plan['branches']:
  for window in WINDOWS:
   for key,index in [('bias_hz',0),('mae_hz',1),('dose_mean_pA',None),('total_mean_pA',None),('total_charge_pC',None)]:
    vals=[np.mean([all_scores[n,k,cond,name,window][index] if index is not None else float(mi[n,k,cond,name,window][key]) for k in (45,46)]) for n in range(10)];saved=summary['models'][cond+'_'+name][window][key];close(saved['mean'],np.mean(vals));close(saved['ci95'],boot(vals));close(saved['network_values'],vals)
 for cond in ('STATIC','LOSS'):
  vals=[np.mean([all_scores[n,k,cond,'FIXED','late'][1]-all_scores[n,k,cond,'PI10_5','late'][1] for k in (45,46)]) for n in range(10)];close(summary['comparisons'][cond]['ci95'],boot(vals));close(summary['comparisons'][cond]['pi_vs_fixed_mae_benefit_hz'],np.mean(vals))
 samples=[json.loads(x) for x in (R/'resource_samples.jsonl').read_text().splitlines()]
 assert samples and all(not x['faults'] and x['clock_id']==meta['deadline_clock_id'] and x['allocated_bytes']<=500*1024**2 and x['new_evidence_allocated_bytes']<=150*1024**2 and x['peak_rss_bytes']<2*1024**3 and all(v<2*1024**3 for v in x['rss_bytes'].values()) for x in samples)
 result=dict(status='PASS',trials=20,branches=100,observation_bins=320000,metrics=800,traces=6400,moving_windows=5700,progress_segments=segments,independent_updates=6400,clock_id=meta['deadline_clock_id'],source_revision=meta['head'],max_concurrent_workers=peak,wall_s=time.perf_counter()-began,scientific=summary['scientific_pass'],m005b='HOLD')
 (R/'verification.json').write_text(json.dumps(result,indent=2)+'\n');Deadline.from_environment().check()
if __name__=='__main__':main()
