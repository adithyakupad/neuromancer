"""M004 evaluator. Gain/paired shams only here, after online forecast seals."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.online_identify import NAMES, features, standardized
from neuromancer.calibration_diagnostic import save_json
from select_models import scores, detection

ALL_NAMES=(*NAMES,'ORACLE')


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def boot(x):
    x=np.asarray(x,float);draw=np.random.default_rng(20261104).integers(0,len(x),(10000,len(x)))
    return np.quantile(x[draw].mean(axis=1),[.025,.975],axis=0).tolist()


def adaptation_gate(frozen,adapt,stationary_frozen,stationary_adapt,pre_frozen,pre_adapt):
    delta=frozen-adapt;relative=delta/np.maximum(frozen,.04);harm=(stationary_adapt-stationary_frozen)/np.maximum(stationary_frozen,.04)
    pre=(pre_adapt-pre_frozen)/np.maximum(pre_frozen,.04);ci=boot(delta);hc=boot(harm);required=8 if len(delta)==10 else 4
    points=delta.mean()>=.04 and relative.mean()>=.1 and (delta>0).sum()>=required and harm.mean()<=.05 and pre.mean()<=.05
    passed=points and ci[0]>0 and hc[1]<=.1
    return dict(decision='PASS' if passed else 'HOLD' if points else 'FAIL',absolute_benefit_hz2=float(delta.mean()),absolute_ci=ci,
        relative_benefit=float(relative.mean()),relative_ci=boot(relative),positive_networks=int((delta>0).sum()),
        stationary_relative_harm=float(harm.mean()),stationary_harm_ci=hc,prechange_relative_harm=float(pre.mean()),
        denominator_floors=int((frozen<.04).sum()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--dev',type=Path,required=True);p.add_argument('--dev-replay',type=Path,required=True)
    p.add_argument('--validation',type=Path,required=True);p.add_argument('--validation-replay',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();began=time.perf_counter()
    choice=json.loads(args.selection.read_text());model=choice['adaptation']['index'];det=choice['detector']['index']
    args.output.mkdir(parents=True,exist_ok=False);rows=[];effect_rows=[];alarm_rows=[];block_rows=[];failure_rows=[];metrics={};detmetrics={};coefficient_rows=[];one_rows=[];window_rows=[];recovery_rows=[]
    for raw,replay,stage in ((args.dev,args.dev_replay,'D'),(args.validation,args.validation_replay,'V')):
        seal=json.loads((replay/'seal.json').read_text())
        for name,h in seal['artifact_sha256'].items():assert hashlib.sha256((replay/name).read_bytes()).hexdigest()==h
        for folder in sorted(raw.glob('n*_r*')):
            identity=folder.name;metadata=json.loads((folder/'trial.json').read_text());n=metadata['network_id'];rep=metadata['replicate_id'];condition=metadata['condition']
            public=np.load(folder/'public.npz');u=public['delivered'];y=public['rates'];ev=np.load(folder/'evaluator.npz');gain=ev['gain']
            online=np.load(replay/identity/'online.npz');init=json.loads((replay/identity/'initial.json').read_text());record=init['fir']
            future=online['rolling'];truth=y[1950:].reshape(40,50,4);oracle=[]
            effective=u*gain[:,None]
            for k in range(1950,3950,50):oracle.append(standardized(record,features(effective,np.arange(k,k+50)))@np.array(record['coef'])+record['output_mean'])
            prediction=np.concatenate([future,np.array(oracle)[None]],axis=0);err=prediction.mean(axis=2)-truth.mean(axis=1)
            mse=(err**2).mean(axis=2);metrics[identity]=dict(mse=mse,n=n,rep=rep,condition=condition,stage=stage)
            for m,name in enumerate(ALL_NAMES):
                for b,k in enumerate(range(1950,3950,50)):
                    rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,model=name,origin_s=k/50,
                        mse_hz2=float(mse[m,b]),bias_hz=float(err[m,b].mean()),mae_hz=float(abs(err[m,b]).mean()),
                        coverage=float(np.mean(abs(err[m,b])<=online['width'])),interval_mean_halfwidth_hz=float(online['width'].mean()),
                        mean_total_pA=float(u[k:k+50].sum(axis=1).mean())))
            for m,name in enumerate(NAMES):
                for label,sl in (('pre',slice(0,1000)),('post',slice(1000,2000))):
                    er=online['one_step'][m,sl]-y[1950:][sl]
                    one_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,model=name,window=label,mse_hz2=float(np.mean(er**2)),bias_hz=float(er.mean()),mae_hz=float(abs(er).mean())))
            for m,name in enumerate(ALL_NAMES):
                for label,sl in (('pre',slice(0,20)),('post0-5',slice(20,25)),('post5-10',slice(25,30)),('post10-20',slice(30,40))):
                    er=err[m,sl]
                    window_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,model=name,window=label,mse_hz2=float(np.mean(er**2)),bias_hz=float(er.mean()),coverage=float(np.mean(abs(er)<=online['width']))))
            if condition=='LOSS':
                recovered=False;delay=20.
                for end in range(25,41):
                    sl=slice(end-5,end)
                    if (abs(err[model,sl].mean(axis=1))<=.2).all() and mse[model,sl].mean()<=mse[0,sl].mean():
                        recovered=True;delay=float(end-20);break
                recovery_rows.append(dict(stage=stage,network=n,replicate=rep,model=ALL_NAMES[model],recovered=recovered,delay_s=delay))
            for j,origin in enumerate((54,64,74)):
                k=origin*50;active=np.load(folder/f'probe{origin}_active.npz');sham=np.load(folder/f'probe{origin}_sham.npz')
                np.testing.assert_array_equal(active['rates'],y[k:k+50]);actual=(active['rates']-sham['rates']).mean(axis=0)
                forecasts=online['contrast'][:,j,0].mean(axis=1)-online['contrast'][:,j,1].mean(axis=1)
                plans=np.load(folder/f'probe{origin}_plans.npz')['planned'];oracle_contrast=[]
                for action in plans:
                    fu=np.vstack([effective[k-9:k],action*gain[k:k+50,None]])
                    xx=features(fu,np.arange(9,59));oracle_contrast.append((standardized(record,xx)@np.array(record['coef'])+record['output_mean']).mean(axis=0))
                forecasts=np.vstack([forecasts,np.array(oracle_contrast[0])-oracle_contrast[1]])
                for m,name in enumerate(ALL_NAMES):
                    effect_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,origin_s=origin,model=name,
                        mse_hz2=float(np.mean((forecasts[m]-actual)**2)),bias_hz=float(np.mean(forecasts[m]-actual)),
                        actual_effect_hz=float(actual.mean()),predicted_effect_hz=float(forecasts[m].mean())))
            dd=detection(online['detector'][det,:,2]);fa=float(online['detector'][det,:,2].sum()*1.5)
            window=any(59<t<=69 for t in dd['alarms']);detmetrics[identity]=dict(**dd,false_alarms_per_minute=fa,window_probability=float(window),n=n,rep=rep,condition=condition)
            alarm_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,**{k:v for k,v in dd.items() if k!='alarms'},
                alarms_s=json.dumps(dd['alarms']),stationary_alarms_per_minute=fa if condition in ('STATIC','NULL') else '',
                event_precision=(float(not dd['miss'])/len(dd['alarms']) if dd['alarms'] and condition=='LOSS' else 0.),total_alarms=len(dd['alarms'])))
            residual=prediction[0].mean(axis=(1,2))-truth.mean(axis=(1,2))
            for b in range(40):
                amp=float(u[1950+b*50:2000+b*50].sum(axis=1).mean());stratum='low<60' if amp<60 else 'middle60-120' if amp<120 else 'high>=120'
                block_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,end_s=40+b,amplitude_stratum=stratum,
                    mean_total_pA=amp,residual_hz=float(residual[b]),statistic=float(online['detector'][det,b,0]),
                    armed=bool(online['detector'][det,b,1]),alarm=bool(online['detector'][det,b,2])))
            meta=json.loads((replay/identity/'replay.json').read_text())
            for name,status in meta['models'].items():failure_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,model=name,**{k:v for k,v in status.items() if k!='failures'},failures=json.dumps(status['failures'])))
            for m,name in enumerate(NAMES[:-1]):
                for b in range(41):
                    value=online['kernel_gain_proxy'][m,b]
                    coefficient_rows.append(dict(stage=stage,network=n,replicate=rep,condition=condition,model=name,time_s=39+b,
                        coefficient_norm=float(online['coefficient_norm'][m,b]),kernel_gain_proxy=float(value) if np.isfinite(value) else '',
                        true_gain=float(gain[min((39+b)*50,3949)]),baseline_hz=float(online['baseline'][m,b].mean()),updates=int(online['update_counts'][m,b])))
    summary={};network_rows=[]
    for stage,ns,reps in (('D',range(10),(33,)),('V',range(10,15),(32,33))):
        def array(condition,part):
            return np.array([np.mean([metrics[f'n{n}_r{r}_{condition}']['mse'][:,part].mean(axis=1) for r in reps],axis=0) for n in ns])
        post=array('LOSS',slice(20,40));static=array('STATIC',slice(20,40));pre=array('LOSS',slice(0,20))
        h1=adaptation_gate(post[:,0],post[:,model],static[:,0],static[:,model],pre[:,0],pre[:,model])
        sensitivity=[];delays=[];false=[];window=[]
        for n in ns:
            changed=[detmetrics[f'n{n}_r{r}_LOSS'] for r in reps];station=[detmetrics[f'n{n}_r{r}_STATIC'] for r in reps]
            sensitivity.append(np.mean([d['timely'] for d in changed]));delays.append(np.mean([d['delay_s'] for d in changed]));false.append(np.mean([d['false_alarms_per_minute'] for d in station]));window.append(np.mean([d['window_probability'] for d in station]))
        sensitivity=np.array(sensitivity);false=np.array(false);window=np.array(window);diff=sensitivity-window;fa_ci=boot(false);diff_ci=boot(diff)
        h2_pass=sensitivity.mean()>=.8 and np.median(delays)<=10 and false.mean()<=1 and fa_ci[1]<=2 and diff_ci[0]>0
        h2=dict(decision='PASS' if h2_pass else 'FAIL',sensitivity_by10s=float(sensitivity.mean()),sensitivity_ci=boot(sensitivity),
                median_network_mean_censored_delay_s=float(np.median(delays)),stationary_false_alarms_per_minute=float(false.mean()),
                false_alarm_ci=fa_ci,stationary_window_probability=float(window.mean()),sensitivity_minus_stationary_window_ci=diff_ci)
        summary[stage]=dict(adaptation=h1,detection=h2,post_mean_mse_hz2={name:float(post[:,m].mean()) for m,name in enumerate(ALL_NAMES)},
            stationary_mean_mse_hz2={name:float(static[:,m].mean()) for m,name in enumerate(ALL_NAMES)},pre_mean_mse_hz2={name:float(pre[:,m].mean()) for m,name in enumerate(ALL_NAMES)},
            individual_adaptation={NAMES[m]:adaptation_gate(post[:,0],post[:,m],static[:,0],static[:,m],pre[:,0],pre[:,m]) for m in range(1,5)})
        for j,n in enumerate(ns):
            for m,name in enumerate(ALL_NAMES):network_rows.append(dict(stage=stage,network=n,model=name,post_mse_hz2=float(post[j,m]),stationary_mse_hz2=float(static[j,m]),pre_mse_hz2=float(pre[j,m]),
                loss_detection_by10s=float(sensitivity[j]),censored_delay_s=float(delays[j]),stationary_false_alarms_per_minute=float(false[j])))
    decisions=[summary[s]['adaptation']['decision'] for s in ('D','V')]
    summary['adaptation_decision']='FAIL' if 'FAIL' in decisions else 'HOLD' if 'HOLD' in decisions else 'PASS'
    summary['detection_decision']='PASS' if all(summary[s]['detection']['decision']=='PASS' for s in ('D','V')) else 'FAIL'
    summary['selected_model']=NAMES[model];summary['selected_detector']=choice['detector'];summary['analysis_wall_s']=time.perf_counter()-began
    for name,table in (('rolling',rows),('effects',effect_rows),('detections',alarm_rows),('detector_blocks',block_rows),('failures',failure_rows),('coefficients',coefficient_rows),('networks',network_rows),('one_step',one_rows),('windows',window_rows),('recovery',recovery_rows)):
        write_csv(args.output/f'{name}.csv',table)
    save_json(args.output/'comparison.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
