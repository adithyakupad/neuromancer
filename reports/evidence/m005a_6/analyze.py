"""Retrospective metrics only; no controller fitting, neural simulation or tuning."""
import csv,json,math
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent;RAW=Path('reports/evidence/m005a_5/confirmation')
WINDOWS={'pre':(8,16),'immediate':(16,20),'late':(20,32),'final':(28,32)}
def write(name,rows):
 with (R/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def mean(rows,key):return float(np.mean([r[key] for r in rows]))
def ci(values):
 x=np.asarray(values);g=np.random.Generator(np.random.PCG64(20261025));return np.quantile(x[g.integers(0,len(x),(10000,len(x)))].mean(1),[.025,.975]).tolist()
def wilson(k,n):
 if n==0:return None
 z=1.95996398454;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [max(0.,float(c-h)),min(1.,float(c+h))]
def main():
 Deadline.from_environment().check();windows=[];times=[];trials=[];effects=[];designs=[]
 for folder in sorted(RAW.glob('n*_r*')):
  meta=json.loads((folder/'trial.json').read_text());n,k=meta['network_id'],meta['replicate_id'];c=meta['calibration'];cache={}
  prefix=dict(np.load(folder/'prefix.npz'));bs=prefix['counts'][350:750].reshape(400,4,5)[:,:,:4].sum((0,2))/160.
  for b in meta['branches']:
   cond,name=b['condition'],b['controller'];d=dict(np.load(folder/f'{cond}_{name}.npz'));u=d['delivered'];de=d['decisions']
   sector=d['counts'].reshape(32,50,4,5)[:,:,:,:4].sum((1,3))/20.;y=sector.mean(1);err=y-c['target_hz'];cache[cond,name]=(y,d)
   for second in range(32):
    row=dict(network=n,replicate=k,condition=cond,controller=name,second=second,available_us=52000000+second*1000000,rate_hz=float(y[second]),target_hz=c['target_hz'],signed_error_hz=float(err[second]),desired_q_pA=float(de[second,1]),integral_pA=float(de[second,2]),controller_previous_error_hz=float(de[second,3]) if second else None,blocked=int(de[second,4]),clipped=int(de[second,5]))
    for channel in range(4):row[f'u{channel}_pA']=float(u[second*50:(second+1)*50,channel].mean());row[f'sector{channel}_hz']=float(sector[second,channel]);row[f'sector{channel}_above_baseline_hz']=float(sector[second,channel]-bs[channel])
    row['total_pA']=sum(row[f'u{i}_pA'] for i in range(4));times.append(row)
   for w,(a,z) in WINDOWS.items():
    v=u[a*50:z*50];e=err[a:z];row=dict(network=n,replicate=k,condition=cond,controller=name,window=w,bias_hz=float(e.mean()),mae_hz=float(abs(e).mean()),rate_hz=float(y[a:z].mean()),target_hz=c['target_hz'],baseline_hz=c['baseline_hz'],qff_pA=c['feedforward_pA'],total_mean_pA=float(v.sum(1).mean()),dose_min_pA=float(v[:,0].min()),dose_max_pA=float(v[:,0].max()),dose_zero_fraction=float((v[:,0]==0).mean()),dose_max_fraction=float((v[:,0]==120).mean()),budget_fraction=float((v.sum(1)==240).mean()),exposure_pA_s=float(v.sum()*.02),decision_clip_count=int(de[a:z,5].sum()),antiwindup_count=int(de[a:z,4].sum()),integral_mean_pA=float(de[a:z,2].mean()))
    for ch in range(4):row[f'u{ch}_pA']=float(v[:,ch].mean());row[f'sector{ch}_hz']=float(sector[a:z,ch].mean());row[f'sector{ch}_above_baseline_hz']=float(sector[a:z,ch].mean()-bs[ch])
    windows.append(row)
   for w,a in [('full',0),('last16',800)]:
    v=u[a:];x=(v-v.mean(0))/np.maximum(v.std(0),1.);X=np.column_stack([np.ones(len(x)-9)]+[x[9-j:len(x)-j] for j in range(10)]);sv=np.linalg.svd(X,compute_uv=False);pos=sv[sv>max(X.shape)*np.finfo(float).eps*sv[0]]
    designs.append(dict(network=n,replicate=k,condition=cond,controller=name,window=w,rank=len(pos),features=41,full_condition=None if len(pos)<41 else float(pos[0]/pos[-1]),positive_condition=float(pos[0]/pos[-1]),q_sd_pA=float(v[:,0].std()),changed_ticks=int(np.any(np.diff(v,axis=0)!=0,axis=1).sum()),singular_values=sv.tolist()))
  # Evaluator-only matched contrasts; never available to a policy.
  for name in ('ZERO','FIXED','MAX','PI10_5'):
   yl,dl=cache['LOSS',name];ys,ds=cache['STATIC',name]
   assert np.array_equal(dl['counts'][:800],ds['counts'][:800]);assert np.array_equal(dl['delivered'][:800],ds['delivered'][:800])
   for second in range(32):effects.append(dict(network=n,replicate=k,controller=name,second=second,loss_minus_static_hz=float(yl[second]-ys[second]),loss_minus_zero_hz=float(yl[second]-cache['LOSS','ZERO'][0][second]),static_minus_zero_hz=float(ys[second]-cache['STATIC','ZERO'][0][second])))
  y,d=cache['LOSS','PI10_5'];de=d['decisions'];e=c['target_hz']-y;term=d['terminal'];blocked=int(de[:,4].sum()+term[4]);clipped=int(de[:,5].sum()+term[5]);clamps=0
  for i in range(32):
   proposed=de[i,2]+5*e[i];clamps+=int(abs(proposed)>120)
  maxmargin=float((cache['LOSS','MAX'][0][20:]-c['target_hz']).mean());zeromargin=float((cache['LOSS','ZERO'][0][20:]-c['target_hz']).mean())
  t=dict(network=n,replicate=k,target_hz=c['target_hz'],baseline_hz=c['baseline_hz'],noise_hz=c['noise_hz'],slope_hz_per_pA=c['slope_hz_per_pA'],qff_pA=c['feedforward_pA'],gain_scaled_reference_pA=c['feedforward_pA']/.6,max_target_margin_hz=maxmargin,zero_target_margin_hz=zeromargin,bracket=zeromargin<0<maxmargin,pi_pre_bias_hz=float((y[8:16]-c['target_hz']).mean()),pi_immediate_bias_hz=float((y[16:20]-c['target_hz']).mean()),pi_late_bias_hz=float((y[20:]-c['target_hz']).mean()),pi_final_bias_hz=float((y[28:]-c['target_hz']).mean()),pi_q_peak_pA=float(d['delivered'][:,0].max()),pi_dose_bound_ticks=int(((d['delivered'][:,0]==0)|(d['delivered'][:,0]==120)).sum()),clipped_including_terminal=clipped,blocked_including_terminal=blocked,integral_clamp_attempts=clamps,integral_post_delta_pA=float(term[2]-de[16,2]),post_error_integral_pA=float(5*e[16:].sum()),late_error_integral_pA=float(5*e[20:].sum()),late_integral_delta_pA=float(term[2]-de[20,2]))
  for index in (16,17,20,31):t[f'q{index}_pA']=float(de[index,1]);t[f'I{index}_pA']=float(de[index,2])
  t['q32_unused_pA']=float(term[1]);t['I32_pA']=float(term[2]);trials.append(t)
 write('windows.csv',windows);write('timecourses.csv',times);write('matched_effects.csv',effects);write('trial_diagnosis.csv',trials);(R/'excitation.json').write_text(json.dumps(designs,indent=2)+'\n')
 original=list(csv.DictReader(open('reports/evidence/m005a_5/confirmation_analysis/network_qualification.csv')));net=[]
 for n in range(10):
  ts=[t for t in trials if t['network']==n];g=next(v for v in original if int(v['network'])==n and v['condition']=='LOSS');failed=g['qualified']=='False';bracket=all(t['bracket'] for t in ts)
  row=dict(network=n,loss_failed=failed,classification='A' if failed and bracket else 'C' if failed else 'PASS_NO_FAILURE',both_replicates_bracket=bracket,min_max_target_margin_hz=min(t['max_target_margin_hz'] for t in ts),max_max_target_margin_hz=max(t['max_target_margin_hz'] for t in ts),mean_max_target_margin_hz=mean(ts,'max_target_margin_hz'))
  for key in trials[0]:
   if key not in ('network','replicate','bracket','max_target_margin_hz'):row[key]=mean(ts,key)
  for cond in ('STATIC','LOSS'):
   for name in ('ZERO','FIXED','MAX','PI10_5'):
    for w in WINDOWS:
     v=[x for x in windows if x['network']==n and x['condition']==cond and x['controller']==name and x['window']==w]
     for key in ('bias_hz','mae_hz','total_mean_pA','integral_mean_pA'):row[f'{cond}_{name}_{w}_{key}']=mean(v,key)
  row['pi_loss_mae_benefit_hz']=row['LOSS_FIXED_late_mae_hz']-row['LOSS_PI10_5_late_mae_hz'];row['pi_bias_improvement_final_vs_immediate_hz']=row['pi_final_bias_hz']-row['pi_immediate_bias_hz'];net.append(row)
 write('network_diagnosis.csv',net)
 stats={}
 for key in ('pi_pre_bias_hz','pi_immediate_bias_hz','pi_late_bias_hz','pi_final_bias_hz','mean_max_target_margin_hz','pi_loss_mae_benefit_hz','pi_bias_improvement_final_vs_immediate_hz'):
  x=[v[key] for v in net];stats[key]=dict(mean=float(np.mean(x)),ci95=ci(x),network_values=x)
 classifications={k:dict(count=sum(v['classification']==k for v in net),fraction=sum(v['classification']==k for v in net)/10,wilson95=wilson(sum(v['classification']==k for v in net),10)) for k in ('A','B','C','PASS_NO_FAILURE')}
 # Correlations are descriptive; ranks use average ties, not fitted regression.
 def rank(a):return np.array([sum(b<v for b in a)+(sum(b==v for b in a)-1)/2 for v in a])
 correlations={}
 for key in ('target_hz','baseline_hz','qff_pA','slope_hz_per_pA','mean_max_target_margin_hz','integral_post_delta_pA'):
  x=np.array([v[key] for v in net]);y=np.array([v['pi_late_bias_hz'] for v in net]);correlations[key]=dict(pearson=float(np.corrcoef(x,y)[0,1]),spearman=float(np.corrcoef(rank(x),rank(y))[0,1]),n=10,interpretation='descriptive, confounded; no causal target effect')
 result=dict(stats=stats,classifications=classifications,failed_networks=[v['network'] for v in net if v['loss_failed']],A_conditional_failed=sum(v['classification']=='A' for v in net)/sum(v['loss_failed'] for v in net),both_replicate_brackets=sum(v['both_replicates_bracket'] for v in net),pi_bound_ticks=sum(t['pi_dose_bound_ticks'] for t in trials),clipped=sum(t['clipped_including_terminal'] for t in trials),blocked=sum(t['blocked_including_terminal'] for t in trials),integral_clamp_attempts=sum(t['integral_clamp_attempts'] for t in trials),correlations=correlations,new_scientific_neural_acquisition=0,m005b='HOLD')
 (R/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');Deadline.from_environment().check()
if __name__=='__main__':main()
