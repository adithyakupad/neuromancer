"""Frozen M005A scoring; only completed trajectories, network-level inference."""
import argparse
import csv
import json
from pathlib import Path
import time
import numpy as np


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')


def ci(x):
    x = np.asarray(x, float)
    rng = np.random.Generator(np.random.PCG64(20261025))
    samples = x[rng.integers(0,len(x),(10000,len(x)))].mean(axis=1)
    return [float(v) for v in np.quantile(samples,[.025,.975])]


def excitation(u):
    scale=np.maximum(u.std(axis=0),1.)
    x=(u-u.mean(axis=0))/scale
    design=np.column_stack([np.ones(len(x)-9)]+[x[9-j:len(x)-j] for j in range(10)])
    singular=np.linalg.svd(design,compute_uv=False)
    positive=singular[singular>max(design.shape)*np.finfo(float).eps*singular[0]]
    return dict(rank=len(positive),features=41,singular_values=singular.tolist(),
                full_condition=None if len(positive)<41 else float(positive[0]/positive[-1]),
                positive_condition=float(positive[0]/positive[-1]),
                per_channel_sd_pA=u.std(axis=0).tolist(),per_channel_unique=[len(np.unique(v)) for v in u.T],
                changed_ticks=int(np.any(np.diff(u,axis=0)!=0,axis=1).sum()))


def trial_rows(folder):
    meta=json.loads((folder/'trial.json').read_text()); c=meta['calibration']; records=[]; traces=[]; designs=[]
    for b in meta['branches']:
        condition,name=b['condition'],b['controller']
        with np.load(folder/f'{condition}_{name}.npz') as d:
            raw=d['counts'].reshape(1600,4,5)[:,:,:4].sum(axis=(1,2))/1.6
            seconds=raw.reshape(32,50).mean(axis=1); error=seconds-c['target_hz']; u=d['delivered']; dec=d['decisions']
            windows={'full':(0,32),'stationary':(8,32),'pre':(8,16),'immediate':(16,20),'late':(20,32)}
            for window,(a,z) in windows.items():
                e=error[a:z]; records.append(dict(network=meta['network_id'],replicate=meta['replicate_id'],condition=condition,
                    controller=name,window=window,mae_hz=float(abs(e).mean()),bias_hz=float(e.mean()),rmse_hz=float(np.sqrt((e*e).mean())),
                    rate_hz=float(seconds[a:z].mean()),target_hz=c['target_hz'],baseline_hz=c['baseline_hz'],noise_hz=c['noise_hz'],
                    calibration_valid=c['valid'],online_exposure_pA_s=float(u.sum()*.02),
                    calibration_exposure_pA_s=meta['prefix_audit']['exposure_pA_s'],
                    total_charge_pC=50*(float(u.sum()*.02)+meta['prefix_audit']['exposure_pA_s']),
                    current_squared_pA2_s=float((u*u).sum()*.02),saturation_fraction=float(dec[:,5].mean()),
                    fallback_decisions=int(dec[:,6].sum()),controller_wall_ns=int(d['timings_ns'][:,:2].sum()),
                    terminal_integral_pA=float(d['terminal'][2])))
            for second,y in enumerate(seconds): traces.append(dict(network=meta['network_id'],replicate=meta['replicate_id'],condition=condition,controller=name,second=second,rate_hz=float(y),target_hz=c['target_hz'],q_pA=float(dec[second,1]),integral_pA=float(dec[second,2])))
            for window,a in [('full',0),('last16',800)]:
                designs.append(dict(network=meta['network_id'],replicate=meta['replicate_id'],condition=condition,controller=name,window=window,**excitation(u[a:])))
    return records,traces,designs


def csvout(path, rows):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def lookup(rows,n,controller,condition,window,key):
    return float(np.mean([r[key] for r in rows if (r['network'],r['controller'],r['condition'],r['window'])==(n,controller,condition,window)]))


def network_gates(rows, selected):
    out=[]
    for n in range(10):
        relevant=[r for r in rows if r['network']==n]
        valid=all(r['calibration_valid'] and 1<=r['baseline_hz']<=30 and r['fallback_decisions']==0 for r in relevant)
        # Duplicated rows across policies/windows do not change this replicate RMS.
        noise=float(np.sqrt(np.mean([r['noise_hz']**2 for r in relevant])))
        for condition,window in [('STATIC','stationary'),('LOSS','late')]:
            mae=lookup(rows,n,selected,condition,window,'mae_hz');zero=lookup(rows,n,'ZERO',condition,window,'mae_hz')
            fixed=lookup(rows,n,'FIXED',condition,window,'mae_hz');bias=lookup(rows,n,selected,condition,window,'bias_hz')
            authority=lookup(rows,n,'MAX',condition,'late','rate_hz')-lookup(rows,n,'ZERO',condition,'late','rate_hz')
            components=dict(calibration_baseline_valid=valid,noise_valid=1>=2*noise,authority=authority>=1.2,
                            error=mae<=.35,bias=abs(bias)<=.2,zero_benefit=(zero-mae)/max(zero,.1)>=.3)
            out.append(dict(network=n,condition=condition,mae_hz=mae,fixed_mae_hz=fixed,zero_mae_hz=zero,bias_hz=bias,
                            authority_hz=authority,noise_hz=float(noise),**components,qualified=all(components.values())))
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--selection',type=Path);args=p.parse_args();args.output.mkdir(exist_ok=False,parents=True);started=time.perf_counter()
    meta=json.loads((args.raw/'provenance.json').read_text());rows=[];traces=[];designs=[]
    for folder in sorted(args.raw.glob('n*_r*')):
        r,t,d=trial_rows(folder);rows+=r;traces+=t;designs+=d
    csvout(args.output/'metrics.csv',rows);csvout(args.output/'traces.csv',traces);save(args.output/'excitation.json',designs)
    candidates={}
    for name in meta['names']:
        if name.startswith('PI'):
            values=[.5*(lookup(rows,n,name,'STATIC','stationary','mae_hz')+lookup(rows,n,name,'LOSS','late','mae_hz')) for n in range(10)]
            candidates[name]=dict(mean_score=float(np.mean(values)),network_scores=values)
    if args.selection is None:
        chosen=min(candidates,key=lambda k:(round(candidates[k]['mean_score'],12),int(k[2:].split('_')[0])))
        save(args.output/'selection.json',dict(frozen=True,controller=chosen,candidates=candidates,stage='TUNE',raw_source_revision=meta['head']))
    else: chosen=json.loads(args.selection.read_text())['controller']
    gates=network_gates(rows,chosen);csvout(args.output/'network_qualification.csv',gates)
    summary=dict(stage=meta['stage'],selected=chosen,models={},regimes={},recovery_advantage={},wall_s=0.)
    for name in meta['names']:
        summary['models'][name]={}
        for condition,window in [('STATIC','stationary'),('LOSS','late')]:
            values=[lookup(rows,n,name,condition,window,'mae_hz') for n in range(10)]
            summary['models'][name][condition]=dict(mae_hz=float(np.mean(values)),ci_hz=ci(values),network_mae_hz=values)
    for condition in ('STATIC','LOSS'):
        g=[r for r in gates if r['condition']==condition]
        benefit=np.array([r['zero_mae_hz']-r['mae_hz'] for r in g]);low=ci(benefit)[0]
        summary['regimes'][condition]=dict(qualified=sum(r['qualified'] for r in g),zero_benefit_ci_hz=ci(benefit),
                                         pass_gate=sum(r['qualified'] for r in g)>=8 and low>0,
                                         component_counts={k:sum(r[k] for r in g) for k in ('calibration_baseline_valid','noise_valid','authority','error','bias','zero_benefit')})
    g=[r for r in gates if r['condition']=='LOSS'];benefit=np.array([r['fixed_mae_hz']-r['mae_hz'] for r in g]);fixed=np.array([r['fixed_mae_hz'] for r in g]);rel=benefit/np.maximum(fixed,.1)
    extra=bool(rel.mean()>=.2 and benefit.mean()>=.1 and ci(benefit)[0]>0 and (benefit>0).sum()>=8)
    summary['recovery_advantage']=dict(mean_absolute_hz=float(benefit.mean()),ci_hz=ci(benefit),mean_relative=float(rel.mean()),relative_ci=ci(rel),positive=int((benefit>0).sum()),denominator_floor_count=int((fixed<.1).sum()),pass_gate=extra)
    summary['stationary_pass']=summary['regimes']['STATIC']['pass_gate'];summary['recovery_pass']=summary['regimes']['LOSS']['pass_gate'] and extra
    summary['scientific_pass']=summary['stationary_pass'] and summary['recovery_pass'];summary['wall_s']=time.perf_counter()-started
    save(args.output/'summary.json',summary)


if __name__=='__main__':main()
