"""Independent aggregation, tuning and paired network gates from archived streams."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from verify import read,xmatrix

NAMES=('FROZEN','SW250','SW500','RLS995','RLS999','SHUFFLED','ARX','ORACLE')


def bounds(v):
    v=np.asarray(v);draw=np.random.Generator(np.random.PCG64(20261104)).integers(0,len(v),(10000,len(v)))
    return np.percentile(v[draw].mean(axis=1),[2.5,97.5],axis=0)


def event(stats):
    times=np.arange(40,80)[stats[:,2].astype(bool)];post=times[times>59]
    return dict(timely=float(len(post)>0 and post[0]<=69),delay=float(post[0]-59) if len(post) else 20.,
                stationary_window=float(np.any((times>59)&(times<=69))),fa=float(len(times)*1.5))


def main():
    p=argparse.ArgumentParser();p.add_argument('--dev',type=Path,required=True);p.add_argument('--dev-replay',type=Path,required=True)
    p.add_argument('--validation',type=Path,required=True);p.add_argument('--validation-replay',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();choice=json.loads(args.selection.read_text());summary=json.loads((args.analysis/'comparison.json').read_text());cache={};checks=0
    for raw,replay in ((args.dev,args.dev_replay),(args.validation,args.validation_replay)):
        for trial in raw.glob('n*_r*'):
            d=read(trial/'public.npz');o=read(replay/trial.name/'online.npz');rec=json.loads((replay/trial.name/'initial.json').read_text())['fir']
            yy=d['rates'][1950:].reshape(40,50,4).mean(axis=1);actual_gain=read(trial/'evaluator.npz')['gain'];u=d['delivered']*actual_gain[:,None]
            beta=np.array(rec['coef']);base=np.array(rec['output_mean'])+beta[0]-(np.array(rec['mean'])/rec['scale'])@beta[1:];b=beta[1:]/np.array(rec['scale'])[:,None]
            oracle=np.array([(base+xmatrix(u,np.arange(k,k+50))@b).mean(axis=0) for k in range(1950,3950,50)])
            pred=np.concatenate([o['rolling'].mean(axis=2),oracle[None]],axis=0);mse=np.square(pred-yy).mean(axis=2)
            cache[trial.name]=dict(mse=mse,events=[event(s) for s in o['detector']],pred=pred,actual=yy,o=o)
    # Recompute adaptation tuning using only noise32 and the four registered candidates.
    tuning=[]
    for m in range(1,5):
        loss=np.array([cache[f'n{n}_r32_LOSS']['mse'][:,20:].mean(axis=1) for n in range(10)])
        stationary=np.array([cache[f'n{n}_r32_STATIC']['mse'][:,20:].mean(axis=1) for n in range(10)])
        pre=np.array([cache[f'n{n}_r32_LOSS']['mse'][:,:20].mean(axis=1) for n in range(10)])
        harm=np.mean((stationary[:,m]-stationary[:,0])/np.maximum(stationary[:,0],.04));ph=np.mean((pre[:,m]-pre[:,0])/np.maximum(pre[:,0],.04))
        tuning.append((m,loss[:,m].mean(),harm,ph,harm<=.05 and ph<=.05))
    valid=[r for r in tuning if r[4]] or tuning;minimum=min(r[1] for r in valid);priority={1:(0,-250),2:(0,-500),3:(1,-.995),4:(1,-.999)}
    selected=min((r for r in valid if r[1]<=minimum+1e-12),key=lambda r:priority[r[0]])[0];assert selected==choice['adaptation']['index']
    detector=[]
    for j,(nu,h) in enumerate(( (nu,h) for nu in (.25,.5) for h in (3,5,8,12))):
        false=np.mean([cache[f'n{n}_r32_STATIC']['events'][j]['fa'] for n in range(10)])
        sens=np.mean([cache[f'n{n}_r32_LOSS']['events'][j]['timely'] for n in range(10)])
        delay=np.median([cache[f'n{n}_r32_LOSS']['events'][j]['delay'] for n in range(10)])
        detector.append(dict(j=j,nu=nu,h=h,fa=false,sens=sens,delay=delay))
    feasible=[r for r in detector if r['fa']<=1]
    if feasible:chosen=min(feasible,key=lambda r:(-r['sens'],r['delay'],-r['h'],-r['nu']))
    else:chosen=min(detector,key=lambda r:(r['fa'],-r['sens'],-r['h'],-r['nu']))
    assert chosen['j']==choice['detector']['index'];di=chosen['j']
    # Verify every reported rolling row, effect and ordinary next-bin metric.
    for row in csv.DictReader((args.analysis/'rolling.csv').open()):
        key=f"n{row['network']}_r{row['replicate']}_{row['condition']}";item=cache[key];m=NAMES.index(row['model']);k=int(float(row['origin_s']))-39
        er=item['pred'][m,k]-item['actual'][k]
        np.testing.assert_allclose(float(row['mse_hz2']),np.dot(er,er)/4,atol=1e-11)
        np.testing.assert_allclose(float(row['bias_hz']),sum(er)/4,atol=1e-11);checks+=1
    effect_checks=0
    for raw,replay in ((args.dev,args.dev_replay),(args.validation,args.validation_replay)):
        for trial in raw.glob('n*_r*'):
            item=cache[trial.name];o=item['o'];record=json.loads((replay/trial.name/'initial.json').read_text())['fir'];d=read(trial/'public.npz')
            key=trial.name
            for row in csv.DictReader((args.analysis/'effects.csv').open()):
                if f"n{row['network']}_r{row['replicate']}_{row['condition']}"!=key:continue
                origin=int(row['origin_s']);j=(54,64,74).index(origin);m=NAMES.index(row['model']);k=origin*50
                actual=(read(trial/f'probe{origin}_active.npz')['rates']-read(trial/f'probe{origin}_sham.npz')['rates']).mean(axis=0)
                if m<7:pred=(o['contrast'][m,j,0]-o['contrast'][m,j,1]).mean(axis=0)
                else:
                    gain=read(trial/'evaluator.npz')['gain'];plans=read(trial/f'probe{origin}_plans.npz')['planned'];rawb=np.array(record['coef'])[1:]/np.array(record['scale'])[:,None];responses=[]
                    for action in plans:
                        effective=np.vstack([d['delivered'][k-9:k]*gain[k-9:k,None],action*gain[k:k+50,None]])
                        responses.append((xmatrix(effective,np.arange(9,59))@rawb).mean(axis=0))
                    pred=responses[0]-responses[1]
                np.testing.assert_allclose(float(row['mse_hz2']),np.mean((pred-actual)**2),atol=1e-10);effect_checks+=1
    gates={}
    for stage,ns,reps in (('D',list(range(10)),(33,)),('V',list(range(10,15)),(32,33))):
        def means(condition,part):return np.array([np.mean([cache[f'n{n}_r{r}_{condition}']['mse'][:,part].mean(axis=1) for r in reps],axis=0) for n in ns])
        post=means('LOSS',slice(20,40));station=means('STATIC',slice(20,40));pre=means('LOSS',slice(0,20))
        for m,name in enumerate(NAMES):
            np.testing.assert_allclose(summary[stage]['post_mean_mse_hz2'][name],post[:,m].mean(),atol=1e-11)
        delta=post[:,0]-post[:,selected];relative=delta/np.maximum(post[:,0],.04);harm=(station[:,selected]-station[:,0])/np.maximum(station[:,0],.04);ph=(pre[:,selected]-pre[:,0])/np.maximum(pre[:,0],.04)
        g=summary[stage]['adaptation'];np.testing.assert_allclose(g['absolute_ci'],bounds(delta),atol=1e-12);np.testing.assert_allclose(g['relative_ci'],bounds(relative),atol=1e-12)
        np.testing.assert_allclose(g['stationary_harm_ci'],bounds(harm),atol=1e-12)
        points=delta.mean()>=.04 and relative.mean()>=.1 and (delta>0).sum()>=(8 if stage=='D' else 4) and harm.mean()<=.05 and ph.mean()<=.05
        h1='PASS' if points and bounds(delta)[0]>0 and bounds(harm)[1]<=.1 else 'HOLD' if points else 'FAIL';assert h1==g['decision']
        sensitivity=np.array([np.mean([cache[f'n{n}_r{r}_LOSS']['events'][di]['timely'] for r in reps]) for n in ns])
        false=np.array([np.mean([cache[f'n{n}_r{r}_STATIC']['events'][di]['fa'] for r in reps]) for n in ns])
        window=np.array([np.mean([cache[f'n{n}_r{r}_STATIC']['events'][di]['stationary_window'] for r in reps]) for n in ns])
        delay=np.array([np.mean([cache[f'n{n}_r{r}_LOSS']['events'][di]['delay'] for r in reps]) for n in ns]);d=summary[stage]['detection']
        np.testing.assert_allclose(d['false_alarm_ci'],bounds(false),atol=1e-12);np.testing.assert_allclose(d['sensitivity_minus_stationary_window_ci'],bounds(sensitivity-window),atol=1e-12)
        h2='PASS' if sensitivity.mean()>=.8 and np.median(delay)<=10 and false.mean()<=1 and bounds(false)[1]<=2 and bounds(sensitivity-window)[0]>0 else 'FAIL'
        assert h2==d['decision'];gates[stage]=dict(adaptation=h1,detection=h2)
    result=dict(status='PASS',selection_verified=True,rolling_rows=checks,effect_rows=effect_checks,cohort_decisions=gates,
        selection_sha256=hashlib.sha256(args.selection.read_bytes()).hexdigest(),limitation='Independent equations, same session')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
