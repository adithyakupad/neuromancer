"""Descriptive frozen-endpoint reporting; no model/threshold selection."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np


def rows(path):return list(csv.DictReader(path.open()))


def ci(x):
    x=np.asarray(x);draw=np.random.default_rng(20261104).integers(0,len(x),(10000,len(x)))
    return np.quantile(x[draw].mean(axis=1),[.025,.975]).tolist()


def table(path,records):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)


def main():
    p=argparse.ArgumentParser();p.add_argument('--analysis',type=Path,required=True);p.add_argument('--dev',type=Path,required=True);p.add_argument('--dev-replay',type=Path,required=True)
    p.add_argument('--validation',type=Path,required=True);p.add_argument('--validation-replay',type=Path,required=True);a=p.parse_args();base=a.analysis
    effects=rows(base/'effects.csv');rolling=rows(base/'rolling.csv');alarms=rows(base/'detections.csv');coefficients=rows(base/'coefficients.csv');recoveries=rows(base/'recovery.csv');ordinary=rows(base/'one_step.csv');blocks=rows(base/'detector_blocks.csv')
    summary={};amplitude=[]
    for stage,ns,reps in (('D',range(10),(33,)),('V',range(10,15),(32,33))):
        selected=lambda r:r['stage']==stage and int(r['replicate']) in reps
        post=[r for r in effects if selected(r) and r['condition']=='LOSS' and int(r['origin_s'])>59]
        models=('FROZEN','RLS999','ARX','ORACLE','SHUFFLED');scores={}
        for model in models:scores[model]=np.array([np.mean([float(r['mse_hz2']) for r in post if int(r['network'])==n and r['model']==model]) for n in ns])
        delta=scores['FROZEN']-scores['RLS999'];rr=[r for r in alarms if selected(r) and r['condition']=='LOSS'];station=[r for r in alarms if selected(r) and r['condition']=='STATIC']
        true_events=sum(r['miss']=='False' for r in rr);total=sum(int(r['total_alarms']) for r in rr)
        ss=dict(post_effect_mse_hz2={m:float(x.mean()) for m,x in scores.items()},post_effect_absolute_benefit_hz2=float(delta.mean()),post_effect_benefit_ci=ci(delta),
                late_events=sum(r['late']=='True' for r in rr),missed_events=sum(r['miss']=='True' for r in rr),event_precision=true_events/total if total else None,
                loss_total_alarms=total,loss_prechange_false_alarms=sum(int(r['pre_alarms']) for r in rr),stationary_total_false_alarms=sum(int(r['total_alarms']) for r in station),
                ordinary_post_mse_hz2={m:float(np.mean([float(r['mse_hz2']) for r in ordinary if selected(r) and r['condition']=='LOSS' and r['window']=='post' and r['model']==m])) for m in ('FROZEN','RLS999','ARX')})
        ss['rolling']=[]
        for condition in ('STATIC','LOSS'):
            for model in ('FROZEN','RLS999','ARX'):
                for phase in ('pre','post'):
                    q=[r for r in rolling if selected(r) and r['condition']==condition and r['model']==model and ((float(r['origin_s'])<59)==(phase=='pre'))]
                    ss['rolling'].append(dict(condition=condition,model=model,phase=phase,bias_hz=float(np.mean([float(r['bias_hz']) for r in q])),mae_hz=float(np.mean([float(r['mae_hz']) for r in q])),coverage=float(np.mean([float(r['coverage']) for r in q])),halfwidth_hz=float(np.mean([float(r['interval_mean_halfwidth_hz']) for r in q]))))
        proxy=[];baseline=[]
        for n in ns:
            values=[r for r in coefficients if selected(r) and int(r['network'])==n and r['condition']=='LOSS' and r['model']=='RLS999']
            proxy.append(np.mean([float(r['kernel_gain_proxy']) for r in values if r['time_s']=='79']))
            ends=np.mean([float(r['baseline_hz']) for r in values if r['time_s']=='79']);starts=np.mean([float(r['baseline_hz']) for r in values if r['time_s']=='39']);baseline.append(ends-starts)
        ss['mean_final_kernel_proxy']=float(np.mean(proxy));ss['mean_baseline_change_hz']=float(np.mean(baseline))
        rec=[r for r in recoveries if selected(r)];ss['recovery_fraction']=float(np.mean([r['recovered']=='True' for r in rec]));ss['recovery_censored_median_s']=float(np.median([float(r['delay_s']) for r in rec]))
        for label in ('low<60','middle60-120','high>=120'):
            first=[r for r in blocks if selected(r) and r['condition']=='LOSS' and r['end_s']=='60' and r['amplitude_stratum']==label]
            ids={(r['network'],r['replicate']) for r in first};events=[r for r in rr if (r['network'],r['replicate']) in ids]
            amplitude.append(dict(stage=stage,first_post_block_amplitude=label,trials=len(events),networks=len({r['network'] for r in events}),
                timely_fraction=float(np.mean([r['timely']=='True' for r in events])) if events else '',mean_delay_s=float(np.mean([float(r['delay_s']) for r in events])) if events else '',
                interpretation='Descriptive prescribed-sequence subgroup; later inputs differ; not randomized amplitude effect'))
        summary[stage]=ss
    summary['controls']={}
    for condition in ('UP','NULL','WEAK'):
        rr=[r for r in alarms if r['condition']==condition];q=[r for r in blocks if r['condition']==condition]
        summary['controls'][condition]=dict(trials=len(rr),post_change_alarms=sum(sum(t>59 for t in json.loads(r['alarms_s'])) for r in rr),all_alarms=sum(int(r['total_alarms']) for r in rr),armed_fraction=float(np.mean([r['armed']=='True' for r in q])))
        summary['controls'][condition]['post_mean_mse_hz2']={m:float(np.mean([float(r['mse_hz2']) for r in rolling if r['condition']==condition and r['model']==m and float(r['origin_s'])>=59])) for m in ('FROZEN','RLS999','ARX')}
    performance={};timings={m:dict(forecast=[],update=[]) for m in ('FROZEN','SW250','SW500','RLS995','RLS999','SHUFFLED','ARX')}
    for stage,raw,replay in (('D',a.dev,a.dev_replay),('V',a.validation,a.validation_replay)):
        s=json.loads((raw/'summary.json').read_text());trial=[json.loads(p.read_text()) for p in raw.glob('n*/trial.json')]
        performance[stage]=dict(acquisition_wall_s=s['wall_ns']/1e9,simulated_s=len(trial)*85,peak_worker_rss_bytes=max(t['peak_rss_bytes'] for t in trial),
            initialization_s_range=[min(t['engine']['initialization_ns'] for t in trial)/1e9,max(t['engine']['initialization_ns'] for t in trial)/1e9])
        for f in replay.glob('n*/online.npz'):
            with np.load(f) as d:
                for m,name in enumerate(timings):
                    timings[name]['forecast'].extend(d['forecast_ns'][m].tolist())
                    if m<6:timings[name]['update'].extend(d['update_ns'][m].tolist())
    performance['latency_us']={}
    for name,kind in timings.items():
        performance['latency_us'][name]={}
        for k,values in kind.items():
            if values:
                v=np.array(values)/1000;performance['latency_us'][name][k]=dict(median=float(np.median(v)),p95=float(np.quantile(v,.95)),maximum=float(v.max()),over20ms_fraction=float(np.mean(v>20000)))
    summary['performance']=performance;summary['extra_gates']='None; descriptive aggregation only'
    (base/'report_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');table(base/'amplitude_sensitivity.csv',amplitude)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
