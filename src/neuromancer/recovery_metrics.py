"""Frozen M005A.7 raw-count metrics and finite-horizon gates, never control."""
import numpy as np
WINDOWS={'pre':(8,16),'immediate':(16,20),'original_late':(20,32),'middle':(32,48),'block1':(48,56),'block2':(56,64),'late':(48,64),'full':(0,64)}


def score(errors,window):
    x=np.asarray(errors,float);a,b=window
    if x.shape[-1]!=64 or not np.isfinite(x).all() or not 0<=a<b<=64:raise ValueError('Complete finite64s errors required')
    return float(x[...,a:b].mean()),float(abs(x[...,a:b]).mean())


def regime_gate(replicates,condition):
    if condition not in ('STATIC','LOSS') or len(replicates)!=2 or {r['replicate'] for r in replicates}!={45,46} or len({r['network'] for r in replicates})!=1:raise ValueError('Exactly matched45/46 pair required')
    x=np.array([r['errors'] for r in replicates]);b,m=score(x,(48,64));b1,m1=score(x,(48,56));b2,m2=score(x,(56,64))
    components=dict(calibration=all(r['calibration_valid'] and 1<=r['baseline_hz']<=30 for r in replicates),noise=1>=2*np.sqrt(np.mean([r['noise_hz']**2 for r in replicates])),headroom=True if condition=='STATIC' else np.mean([r['max_target_margin_hz'] for r in replicates])>=.2,bias=abs(b)<=.2,block_bias=abs(b1)<=.2 and abs(b2)<=.2,mae=m<=.35,block_mae=m1<=.35 and m2<=.35,valid=all(not r['fallbacks'] and not r['violations'] for r in replicates))
    return dict(bias_hz=b,mae_hz=m,block1_bias_hz=b1,block2_bias_hz=b2,block1_mae_hz=m1,block2_mae_hz=m2,components={k:bool(v) for k,v in components.items()},qualified=bool(all(components.values())))


def bootstrap(values):
    x=np.asarray(values,float)
    if x.shape!=(10,) or not np.isfinite(x).all():raise ValueError('Ten network means required')
    g=np.random.Generator(np.random.PCG64(20261025));return np.quantile(x[g.integers(0,10,(10000,10))].mean(1),[.025,.975]).tolist()


def cohort_gate(networks):
    if len(networks)!=10:raise ValueError('All ten networks required')
    interval=bootstrap([r['bias_hz'] for r in networks]);count=sum(r['qualified'] for r in networks)
    return dict(qualified=count,bias_ci_hz=interval,pass_gate=bool(count>=8 and interval[0]>=-.2 and interval[1]<=.2))


def recovery_times(errors):
    x=np.asarray(errors,float);score(x,(0,64))
    if x.shape!=(64,):raise ValueError('One trial required')
    hits=[k for k in range(16,62) if (abs(x[k:k+3])<=.35).all()]
    settling=[]
    for end in range(32,65):
        good=True
        for z in range(end,65):
            for a,b in ((z-16,z-8),(z-8,z)):
                bias,mae=score(x,(a,b));good=good and abs(bias)<=.2 and mae<=.35
        if good:settling.append(end)
    return dict(first_recovery_endpoint_s=hits[0]+1-16 if hits else None,recovery_confirmation_s=hits[0]+3-16 if hits else None,settling_delay_s=settling[0]-16 if settling else None,settling_censored=not settling,observed_post_loss_s=48,crossings=int(np.sum(x[16:-1]*x[17:]<0)))
