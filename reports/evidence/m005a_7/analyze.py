"""Frozen M005A.7 endpoints; no controller tuning or scientific acquisition."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from neuromancer.recovery_metrics import WINDOWS,regime_gate,cohort_gate,bootstrap,recovery_times
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent;RAW=R/'trials'
def csvout(path,rows):
 with path.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False);Deadline.from_environment().check()
 metrics=[];traces=[];moving=[];recovery=[];cal=[];seed=[];inputs={};all_violations=0;all_fallbacks=0
 for folder in sorted(RAW.glob('n*_r*')):
  m=json.loads((folder/'trial.json').read_text());assert m['status']=='complete';n,k=m['network_id'],m['replicate_id'];c=m['calibration'];cache={};trial_fallbacks=0;prefix=np.load(folder/'prefix.npz')['delivered'];cal.append(dict(network=n,replicate=k,**c));seed.append(dict(network=n,replicate=k,config=m['engine']['config'],parameter_hashes=m['engine']['metadata']['parameter_hashes'],checkpoint=m['checkpoint'],noise_hashes=m['branches'][0]['noise']))
  for b in m['branches']:
   cond,name=b['condition'],b['controller'];d=dict(np.load(folder/f'{cond}_{name}.npz'));u=d['delivered'];dec=d['decisions'];raw=d['counts'].reshape(3200,4,5)[:,:,:4].sum((1,2))/1.6;y=raw.reshape(64,50).mean(1);err=y-c['target_hz'];cache[cond,name]=err
   fallback=int(dec[:,6].sum());violations=b['audit']['violations'];all_fallbacks+=fallback;trial_fallbacks+=fallback;all_violations+=violations
   for window,(lo,hi) in WINDOWS.items():
    e=err[lo:hi];v=u[lo*50:hi*50];metrics.append(dict(network=n,replicate=k,condition=cond,controller=name,window=window,bias_hz=float(e.mean()),mae_hz=float(abs(e).mean()),rmse_hz=float(np.sqrt((e*e).mean())),rate_hz=float(y[lo:hi].mean()),target_hz=c['target_hz'],baseline_hz=c['baseline_hz'],noise_hz=c['noise_hz'],calibration_valid=c['valid'],dose_mean_pA=float(v[:,0].mean()),total_mean_pA=float(v.sum(1).mean()),window_exposure_pA_s=float(v.sum()*.02),window_current_squared_pA2_s=float((v*v).sum()*.02),dose_zero_fraction=float((v[:,0]==0).mean()),dose_max_fraction=float((v[:,0]==120).mean()),decision_clip_fraction=float(dec[lo:hi,5].mean()),blocked_fraction=float(dec[lo:hi,4].mean()),fallbacks=fallback,violations=violations,total_charge_pC=float((u.sum()+prefix.sum())*.02*50),terminal_integral_pA=float(d['terminal'][2])))
   sector=d['counts'].reshape(64,50,4,5)[:,:,:,:4].sum((1,3))/20
   for sec in range(64):
    v=dict(network=n,replicate=k,condition=cond,controller=name,second=sec,rate_hz=float(y[sec]),target_hz=c['target_hz'],error_hz=float(err[sec]),q_pA=float(dec[sec,1]),integral_pA=float(dec[sec,2]),blocked=int(dec[sec,4]),clipped=int(dec[sec,5]),total_delivered_pA=float(u[sec*50:(sec+1)*50].sum()/50))
    for j in range(4):v[f'sector{j}_hz']=float(sector[sec,j]);v[f'u{j}_pA']=float(u[sec*50:(sec+1)*50,j].mean())
    traces.append(v)
   for end in range(8,65):moving.append(dict(network=n,replicate=k,condition=cond,controller=name,end_second=end,start_second=end-8,bias_hz=float(err[end-8:end].mean()),mae_hz=float(abs(err[end-8:end]).mean())))
   recovery.append(dict(network=n,replicate=k,condition=cond,controller=name,**recovery_times(err)))
  margin=float(cache['LOSS','MAX'][48:].mean())
  for cond in ('STATIC','LOSS'):
   err=cache[cond,'PI10_5'];inputs[n,k,cond]=dict(network=n,replicate=k,errors=err.tolist(),calibration_valid=c['valid'],baseline_hz=c['baseline_hz'],noise_hz=c['noise_hz'],max_target_margin_hz=margin,fallbacks=trial_fallbacks,violations=sum(b['audit']['violations'] for b in m['branches']))
 gates=[];summary=dict(regimes={},models={},comparisons={},fallbacks=all_fallbacks,violations=all_violations)
 for cond in ('STATIC','LOSS'):
  vals=[]
  for n in range(10):
   pair=[inputs[n,k,cond] for k in (45,46)];g=regime_gate(pair,cond);vals.append(g);gates.append(dict(network=n,condition=cond,**{key:value for key,value in g.items() if key not in ('components',)},**g['components'],max_target_margin_hz=float(np.mean([r['max_target_margin_hz'] for r in pair])),noise_rms_hz=float(np.sqrt(np.mean([r['noise_hz']**2 for r in pair])))))
  summary['regimes'][cond]=cohort_gate(vals);summary['regimes'][cond]['component_counts']={key:sum(v['components'][key] for v in vals) for key in vals[0]['components']}
 for cond,name in (('STATIC','PI10_5'),('LOSS','PI10_5'),('STATIC','FIXED'),('LOSS','FIXED'),('LOSS','MAX')):
  model={}
  for window in WINDOWS:
   values={key:[float(np.mean([v[key] for v in metrics if v['network']==n and v['condition']==cond and v['controller']==name and v['window']==window])) for n in range(10)] for key in ('bias_hz','mae_hz','total_mean_pA','dose_mean_pA','total_charge_pC')}
   model[window]={key:dict(mean=float(np.mean(x)),ci95=bootstrap(x),network_values=x) for key,x in values.items()}
  summary['models'][cond+'_'+name]=model
 for cond in ('STATIC','LOSS'):
  pi=summary['models'][cond+'_PI10_5']['late'];fixed=summary['models'][cond+'_FIXED']['late'];benefit=np.array(fixed['mae_hz']['network_values'])-pi['mae_hz']['network_values'];summary['comparisons'][cond]=dict(pi_vs_fixed_mae_benefit_hz=float(benefit.mean()),ci95=bootstrap(benefit),positive=int((benefit>0).sum()))
 summary['recovery_pass']=summary['regimes']['LOSS']['pass_gate'];summary['stationary_pass']=summary['regimes']['STATIC']['pass_gate'];summary['scientific_pass']=bool(summary['recovery_pass'] and summary['stationary_pass'] and all_fallbacks==0 and all_violations==0);summary['m005b']='HOLD';summary['old_m005a5']='FAIL_UNCHANGED'
 csvout(a.output/'metrics.csv',metrics);csvout(a.output/'traces.csv',traces);csvout(a.output/'moving8.csv',moving);csvout(a.output/'recovery.csv',recovery);csvout(a.output/'calibrations.csv',cal);csvout(a.output/'network_qualification.csv',gates)
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(a.output/'seed_manifest.json').write_text(json.dumps(seed,indent=2)+'\n');(a.output/'gate_inputs.json').write_text(json.dumps([dict(condition=c,**v) for (n,k,c),v in inputs.items()],indent=2)+'\n');Deadline.from_environment().check()
if __name__=='__main__':main()
