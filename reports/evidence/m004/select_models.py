"""Tune only development noise32, never reserved33/validation/paired effects."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from neuromancer.calibration_diagnostic import save_json
from neuromancer.online_identify import NAMES
from replay import GRID


def scores(raw, replay, n, rep, condition):
    name=f'n{n}_r{rep}_{condition}'
    with np.load(raw/name/'public.npz') as f:y=f['rates'][1950:].reshape(40,50,4).mean(axis=1)
    with np.load(replay/name/'online.npz') as f:
        prediction=f['rolling'].mean(axis=2);detector=f['detector'].copy()
    mse=((prediction-y)**2).mean(axis=2)
    return mse,detector


def detection(alarms):
    times=np.arange(40,80)[np.asarray(alarms,dtype=bool)];post=times[times>59]
    delay=float(post[0]-59) if len(post) else 20.
    return dict(timely=bool(len(post) and post[0]<=69),delay_s=delay,miss=not len(post),
                alarms=times.tolist(),pre_alarms=int((times<=59).sum()),late=bool(len(post) and post[0]>69))


def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--replay',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();assert not args.output.exists();candidate=[];stationary=[];loss=[];ds=[];dl=[]
    for n in range(10):
        a,b=scores(args.raw,args.replay,n,32,'STATIC');c,d=scores(args.raw,args.replay,n,32,'LOSS');stationary.append(a);loss.append(c);ds.append(b);dl.append(d)
    stationary=np.array(stationary);loss=np.array(loss);ds=np.array(ds);dl=np.array(dl)
    for m in range(1,5):
        sm=stationary[:,:,20:].mean(axis=2);lm=loss[:,:,20:].mean(axis=2);pre=loss[:,:,:20].mean(axis=2)
        harm=float(np.mean((sm[:,m]-sm[:,0])/np.maximum(sm[:,0],.04)));pre_harm=float(np.mean((pre[:,m]-pre[:,0])/np.maximum(pre[:,0],.04)))
        candidate.append(dict(index=m,name=NAMES[m],loss_mse=float(lm[:,m].mean()),stationary_harm=harm,pre_harm=pre_harm,eligible=harm<=.05 and pre_harm<=.05))
    eligible=[r for r in candidate if r['eligible']] or candidate;minimum=min(r['loss_mse'] for r in eligible)
    priority={1:(0,-250),2:(0,-500),3:(1,-.995),4:(1,-.999)}
    selected=min((r for r in eligible if r['loss_mse']<=minimum+1e-12),key=lambda r:priority[r['index']])
    detector_rows=[]
    for j,(nu,h) in enumerate(GRID):
        events=[detection(dl[n,j,:,2]) for n in range(10)];fa=float(ds[:,j,:,2].sum(axis=1).mean()*1.5)
        detector_rows.append(dict(index=j,nu=nu,threshold=h,false_alarms_per_minute=fa,sensitivity=float(np.mean([e['timely'] for e in events])),
                                  median_censored_delay_s=float(np.median([e['delay_s'] for e in events])),eligible=fa<=1))
    feasible=[r for r in detector_rows if r['eligible']]
    if feasible:detector=min(feasible,key=lambda r:(-r['sensitivity'],r['median_censored_delay_s'],-r['threshold'],-r['nu']))
    else:detector=min(detector_rows,key=lambda r:(r['false_alarms_per_minute'],-r['sensitivity'],-r['threshold'],-r['nu']))
    seal=args.replay/'seal.json'
    save_json(args.output,dict(frozen=True,tuning_access='networks0-9/noise32 STATIC and LOSS public observations and sealed online outputs only',
        adaptation=selected,adaptation_candidates=candidate,detector=detector,detector_candidates=detector_rows,
        replay_seal_sha256=hashlib.sha256(seal.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol_sha256=hashlib.sha256(Path('docs/research/008_M004_ONLINE_IDENTIFICATION_PROTOCOL.md').read_bytes()).hexdigest(),
        timing_clarification_sha256=hashlib.sha256(Path('reports/evidence/m004/PREREGISTRATION_CLARIFICATION_001.md').read_bytes()).hexdigest()))
    print(json.dumps(json.loads(args.output.read_text()),indent=2))


if __name__=='__main__':main()
