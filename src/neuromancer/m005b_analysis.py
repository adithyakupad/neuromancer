"""Frozen M005B endpoints; whole-network inference, no controller selection."""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from .supervisor import Deadline,atomic_json
from .recovery_metrics import recovery_times

WINDOWS=dict(full=(0,64),pre=(0,16),post=(16,64),late=(48,64),block1=(48,56),block2=(56,64))


def interval(x):
    x=np.asarray(x,float)
    if x.ndim!=1 or len(x) not in (5,10) or not np.isfinite(x).all():raise ValueError('Complete independent-network values required')
    draws=np.random.Generator(np.random.PCG64(20261105)).integers(0,len(x),(10000,len(x)))
    return dict(mean=float(x.mean()),ci95=np.quantile(x[draws].mean(1),[.025,.975]).tolist(),network_values=x.tolist())


def superiority(reference,adaptive,relative,absolute):
    ref=np.asarray(reference,float);ada=np.asarray(adaptive,float);delta=ref-ada;ab=interval(delta);rel=interval(delta/np.maximum(ref,.01));positive=int((delta>0).sum());minimum=8 if len(ref)==10 else 4
    points=ab['mean']>=absolute and rel['mean']>=relative and positive>=minimum;passed=points and ab['ci95'][0]>0
    return dict(pass_gate=bool(passed),decision='PASS' if passed else 'HOLD' if points else 'FAIL',absolute=ab,relative=rel,positive_networks=positive,required_positive=minimum,denominator_floor_count=int((ref<.01).sum()))


def table(path,rows):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def analyze(root,output):
    root=Path(root);output=Path(output);output.mkdir(exist_ok=False);d=Deadline.from_environment();d.check();metrics=[];traces=[];cal={};model_summaries=[]
    provenance=json.loads((root/'provenance.json').read_text());phase=provenance['phase'];assert phase in ('primary','validation','faults')
    for n,rep in provenance['jobs']:
        folder=root/f'n{n}_r{rep}';trial=json.loads((folder/'trial.json').read_text());initial=json.loads((folder/'initial.json').read_text());c=initial['calibration'];cal[n,rep]=c;prefix=dict(np.load(folder/'prefix.npz'));prefix_exposure=float(prefix['delivered'].sum()*.02)
        for branch in trial['branches']:
            data=dict(np.load(folder/(branch['name']+'.npz')));y=data['counts'].reshape(64,50,4,5)[:,:,:,:4].sum((1,2,3))/80.;errors=y-c['target_hz'];u=data['delivered'];frames=data['frames'];reg=branch['condition'];kind=branch['controller'];fault=branch['fault'] or '';prediction=data['pre_prediction'];raw_y=data['counts'].reshape(3200,4,5)[:,:,:4].sum(2)/.4
            base=dict(network=n,replicate=rep,condition=reg,controller=kind,fault=fault)
            row=base.copy();row.update(calibration_valid=c['valid'],baseline_hz=c['baseline_hz'],noise_hz=c['noise_hz'],target_hz=c['target_hz'],safe_bins=branch['safe_bins'],violations=branch['violations'],model_failure=branch['model_failure'] or '',total_exposure_pA_s=prefix_exposure+float(u.sum()*.02),control_exposure_pA_s=float(u.sum()*.02),model_charge_pC=50*(prefix_exposure+float(u.sum()*.02)),saturated_fraction=float((u[:,0]==120).mean()),dose_zero_fraction=float((u[:,0]==0).mean()),peak_current_pA=float(u.sum(1).max()))
            for name,(a,b) in WINDOWS.items():row[name+'_bias_hz']=float(errors[a:b].mean());row[name+'_mae_hz']=float(abs(errors[a:b]).mean());row[name+'_iae_hz_s']=float(abs(errors[a:b]).sum());row[name+'_exposure_pA_s']=float(u[a*50:b*50].sum()*.02)
            recovery=recovery_times(errors);row.update(settling_delay_s=48 if recovery['settling_censored'] else recovery['settling_delay_s'],settling_censored=recovery['settling_censored'])
            valid=np.isfinite(prediction).all(1);row['prequential_mse_hz2']=float(np.mean((prediction[valid]-raw_y[valid])**2)) if valid.any() else '';metrics.append(row)
            for second in range(64):traces.append(dict(**base,second=second,rate_hz=float(y[second]),error_hz=float(errors[second]),total_mean_pA=float(u[second*50:(second+1)*50].sum()/50),safe_bins=int(frames[second*50:(second+1)*50,2].sum()) if kind.endswith('-MPC') else int(frames[second*50:(second+1)*50,6].sum())))
            if kind.endswith('-MPC'):
                theta=data['dense_theta'];scale=np.array(initial['record']['scale']);B0=np.array(initial['record']['coef'])[1:]/scale[:,None];denom=float((B0*B0).sum());last=theta[-1];B=last[1:]/scale[:,None];zero=np.array(initial['record']['output_mean'])+last[0]-np.array(initial['record']['mean'])@B
                planned_errors=[]
                for plan_index in range(branch['plans']):
                    plan=dict(np.load(folder/f'{branch["name"]}_plan_{plan_index:02}.npz'));origin=(int(plan['origin_us'])-51_000_000)//1_000_000
                    if origin<16 or not data['presented'][origin*50:(origin+1)*50].all() or data['frames'][origin*50:(origin+1)*50,2].any():continue
                    planned_errors.append((plan['selected_forecast'][:50].mean(0)-raw_y[origin*50:(origin+1)*50].mean(0))**2)
                planned_mse=float(np.mean(planned_errors)) if planned_errors else None
                history=np.vstack([np.load(folder/'initial.npz')['history'],u]);x=np.hstack([history[9-j:3209-j] for j in range(10)]);z=np.c_[np.ones(3200),(x-np.array(initial['record']['mean']))/scale];fixed=z@np.array(initial['record']['coef'])+initial['record']['output_mean'];gainproxy=float(np.sum(B*B0)/denom) if denom>1e-12 else None
                windows=[]
                for end in (500,1000,1600,2400,3200):
                    q=np.column_stack([history[9-j+end-500:9-j+end,0] for j in range(10)]);q=(q-q.mean(0))/np.maximum(q.std(0),1);Z=np.c_[np.ones(500),q];rank=int(np.linalg.matrix_rank(Z));condition=float(np.linalg.cond(Z));windows.append(dict(end_bin=end,rank=rank,condition=condition if np.isfinite(condition) else None))
                model_summaries.append(dict(**base,prospective_first_second_post_mse=planned_mse,own_post_mse=float(np.mean((prediction[800:]-raw_y[800:])**2)) if np.isfinite(prediction[800:]).all() else None,frozen_on_same_inputs_post_mse=float(np.mean((fixed[800:]-raw_y[800:])**2)),terminal_kernel_scale_proxy=gainproxy,terminal_zero_input_prediction=zero.tolist(),excitation_windows=windows))
        d.check()
    table(output/'trial_metrics.csv',metrics);table(output/'timecourses.csv',traces);atomic_json(output/'model_diagnostics.json',model_summaries)
    if phase=='faults':atomic_json(output/'summary.json',dict(phase=phase,trials=len(provenance['jobs']),scientific_rescue_permitted=False));return
    networks=sorted({n for n,_ in provenance['jobs']});assert networks==list(range(10)) if phase=='primary' else networks==list(range(10,15))
    def values(reg,kind,key):return np.array([np.mean([float(r[key]) for r in metrics if r['network']==n and r['condition']==reg and r['controller']==kind]) for n in networks])
    h1a=superiority(values('LOSS','PI10_5','post_iae_hz_s'),values('LOSS','RLS-MPC','post_iae_hz_s'),.10,1.2);h1b=superiority(values('LOSS','FIXED-MPC','post_iae_hz_s'),values('LOSS','RLS-MPC','post_iae_hz_s'),.05,.6)
    delay=values('LOSS','PI10_5','settling_delay_s')-values('LOSS','RLS-MPC','settling_delay_s');delay_ci=interval(delay);positive=int((delay>0).sum());recovery=dict(absolute=delay_ci,positive_networks=positive,pass_gate=bool(delay_ci['mean']>=4 and delay_ci['ci95'][0]>0 and positive>=(8 if len(networks)==10 else 4)))
    gates={};qualification=[];minimum=8 if len(networks)==10 else 4
    for kind in ('PI10_5','FIXED-MPC','RLS-MPC'):
        for reg in ('STATIC','LOSS'):
            passed=[];bias=[]
            for n in networks:
                rows=[r for r in metrics if r['network']==n and r['condition']==reg and r['controller']==kind];assert len(rows)==2
                maxrows=[r for r in metrics if r['network']==n and r['condition']=='LOSS' and r['controller']=='MAX'];margin=float(np.mean([r['late_bias_hz'] for r in maxrows]));b=float(np.mean([r['late_bias_hz'] for r in rows]));noise=float(np.sqrt(np.mean([r['noise_hz']**2 for r in rows])))
                components=dict(calibration=all(r['calibration_valid'] and 1<=r['baseline_hz']<=30 for r in rows),noise=1>=2*noise,headroom=reg=='STATIC' or margin>=.2,bias=all(abs(np.mean([r[w+'_bias_hz'] for r in rows]))<=.2 for w in ('late','block1','block2')),mae=all(np.mean([r[w+'_mae_hz'] for r in rows])<=.35 for w in ('late','block1','block2')),valid=all(not r['safe_bins'] and not r['violations'] and not r['model_failure'] for r in rows))
                ok=all(components.values());passed.append(ok);bias.append(b);qualification.append(dict(network=n,condition=reg,controller=kind,bias_hz=b,noise_hz=noise,max_margin_hz=margin,qualified=ok,**components))
            ci=interval(bias);gates[reg+'_'+kind]=dict(qualified=sum(passed),bias=ci,pass_gate=bool(sum(passed)>=minimum and ci['ci95'][0]>=-.2 and ci['ci95'][1]<=.2))
    table(output/'network_qualification.csv',qualification)
    cost={};harm={}
    for reg,window in (('STATIC','full'),('LOSS','post')):
        denominator=values(reg,'PI10_5',window+'_exposure_pA_s');numerator=values(reg,'RLS-MPC',window+'_exposure_pA_s');ratio=interval(numerator/denominator) if (denominator>0).all() else None;cost[reg]=dict(ratio=ratio,pass_gate=bool(ratio is not None and ratio['mean']<=1.10 and ratio['ci95'][1]<=1.15))
    for reg,window in (('STATIC','full'),('LOSS','pre')):
        ref=values(reg,'PI10_5',window+'_iae_hz_s');ada=values(reg,'RLS-MPC',window+'_iae_hz_s');z=interval((ada-ref)/np.maximum(ref,.01));harm[reg]=dict(relative_harm=z,pass_gate=bool(z['mean']<=.05 and z['ci95'][1]<=.10))
    safety=all(not r['safe_bins'] and not r['violations'] and not r['model_failure'] for r in metrics)
    required=[h1a['pass_gate'],h1b['pass_gate'],gates['STATIC_RLS-MPC']['pass_gate'],gates['LOSS_RLS-MPC']['pass_gate'],*[v['pass_gate'] for v in cost.values()],*[v['pass_gate'] for v in harm.values()],safety]
    model_table={}
    for reg in ('STATIC','LOSS'):
        for kind in ('PI10_5','FIXED-MPC','RLS-MPC','BIAS-MPC','FIXED','ZERO'):
            model_table[reg+'_'+kind]={key:interval(values(reg,kind,key)) for key in ('post_iae_hz_s','post_bias_hz','post_mae_hz','late_bias_hz','late_mae_hz','total_exposure_pA_s','post_exposure_pA_s','settling_delay_s')}
    summary=dict(phase=phase,networks=networks,replicates=sorted({r for _,r in provenance['jobs']}),H1a=h1a,H1b=h1b,H2=recovery,H3=gates,H4=cost,H5=harm,safety_pass=safety,scientific_pass=bool(all(required)),execution_numerically_valid=safety,validation_authorized_by_development=bool(all(required)) if phase=='primary' else None,models=model_table,bootstrap_seed=20261105,bootstrap_draws=10000,no_hyperparameter_selection=True)
    atomic_json(output/'summary.json',summary);d.check();print(json.dumps({k:summary[k] for k in ('phase','H1a','H1b','scientific_pass','safety_pass')}))


def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('output');a=p.parse_args();analyze(a.root,a.output)
if __name__=='__main__':main()
