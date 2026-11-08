"""Chronological online replay: opens public observations/plans, never evaluator data."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.calibration_diagnostic import save_json
from neuromancer.diagnostic import provenance
from neuromancer.identify import Predictor
from neuromancer.online_identify import initialize, standardized, features, OnlineFIR, ResidualCUSUM, NAMES, checked

GRID = [(nu, h) for nu in (.25, .5) for h in (3, 5, 8, 12)]


def arx(record, y, u, plan):
    mapped = {k: record[k] for k in ('coef','mean','scale','output_mean','diagnostics')}
    mapped.update(family='ARX',p=4); mapped['diagnostics']={**mapped['diagnostics'],'valid':True}
    return Predictor.load(mapped).forecast(y[-4:],u[-4:],plan)


def planned_features(u, k, plan):
    history=np.vstack([u[k-9:k],plan]);return features(history,np.arange(9,9+len(plan)))


def run_trial(folder, output):
    dest=output/folder.name;dest.mkdir(exist_ok=False);began=time.perf_counter()
    with np.load(folder/'public.npz',allow_pickle=False) as f:
        y=f['rates'].copy();u=f['delivered'].copy();times=f['time_us'].copy();valid=f['valid'].all(axis=1)
    assert len(y)==3950 and np.array_equal(times[:,0],np.arange(3950)*20000)
    with np.load(folder/'plans.npz') as f:plan=f['planned'].copy()
    np.testing.assert_array_equal(u,plan)
    provisional,_,_,_=initialize(y,u,1550)
    residual=[]
    for k in range(1550,1950,50):
        p=standardized(provisional,features(u,np.arange(k,k+50)))@np.array(provisional['coef'])+provisional['output_mean']
        residual.append(p.mean(axis=0)-y[k:k+50].mean(axis=0))
    residual=np.array(residual);sigma=max(float(residual.mean(axis=1).std()),.1);width=np.quantile(abs(residual),.95,axis=0,method='higher')
    record,z,target,p=initialize(y,u);shuffled,sz,st,sp=initialize(y,u,shuffled=True);ar,_,_,_=initialize(y,u,arx=True)
    models=[OnlineFIR(shuffled,sz,st,sp,name) if name=='SHUFFLED' else OnlineFIR(record,z,target,p,name) for name in NAMES[:-1]]
    detectors=[ResidualCUSUM(sigma,nu,h) for nu,h in GRID]
    rolling=np.empty((7,40,50,4));one_step=np.empty((7,2000,4));theta=np.empty((6,41,41,4))
    information=np.empty((2,2,41,41));information[:,0]=np.stack([models[3].p,models[4].p])
    contrast=np.empty((7,3,2,50,4));stats=np.zeros((8,40,3));update_ns=np.zeros((6,2000),np.int64);forecast_ns=np.zeros((7,40),np.int64)
    update_counts=np.zeros((6,41),int);norm=np.zeros((6,41));proxy=np.empty((6,41));baseline=np.empty((6,41,4))
    def snapshot(i):
        for m,model in enumerate(models):
            theta[m,i]=model.theta;update_counts[m,i]=model.updates;norm[m,i]=np.linalg.norm(model.theta)
            b=model.theta[1:]/np.array(model.record['scale'])[:,None];b0=np.array(model.record['coef'])[1:]/np.array(model.record['scale'])[:,None]
            denominator=np.sum(b0*b0);proxy[m,i]=np.sum(b*b0)/denominator if denominator>=1e-12 else np.nan
            baseline[m,i]=model.record['output_mean']+model.theta[0]-(np.array(model.record['mean'])/model.record['scale'])@model.theta[1:]
    snapshot(0)
    for i,k in enumerate(range(1950,3950,50)):
        x=planned_features(u,k,plan[k:k+50])
        for m,model in enumerate(models):
            start=time.perf_counter_ns();rolling[m,i]=model.forecast(x,k*20000);forecast_ns[m,i]=time.perf_counter_ns()-start
        start=time.perf_counter_ns();rolling[6,i]=arx(ar,y[:k],u[:k],plan[k:k+50]);forecast_ns[6,i]=time.perf_counter_ns()-start
        if k//50 in (54,64,74):
            j=(54,64,74).index(k//50);sham=np.maximum(u[k-1][None]-30*np.arange(1,51)[:,None],0)
            sx=planned_features(u,k,sham)
            for m,model in enumerate(models):contrast[m,j]=np.stack([rolling[m,i],model.forecast(sx,k*20000)])
            contrast[6,j]=np.stack([rolling[6,i],arx(ar,y[:k],u[:k],sham)])
        for offset in range(50):
            t=k+offset;row=features(u,np.array([t]))[0]
            for m,model in enumerate(models):
                one_step[m,t-1950]=model.forecast(row[None],t*20000)[0]
                start=time.perf_counter_ns();model.update(row,y[t],int(times[t,1]),int(times[t,2]),bool(valid[t]));update_ns[m,t-1950]=time.perf_counter_ns()-start
            one_step[6,t-1950]=arx(ar,y[:t],u[:t],u[t:t+1])[0]
        e=float((rolling[0,i].mean(axis=0)-y[k:k+50].mean(axis=0)).mean());amp=float(u[k:k+50].sum(axis=1).mean())
        for j,detector in enumerate(detectors):
            d=detector.update(e,amp,(k+50)*20000);stats[j,i]=[d['statistic'],d['armed'],d['alarm']]
        snapshot(i+1)
    information[:,1]=np.stack([models[3].p,models[4].p])
    metadata=dict(status='complete' if not any(m.failed or m.skips for m in models) else 'model_failure',
        models={name:dict(received=m.received,updates=m.updates,refits=m.refits,skips=m.skips,failed=m.failed,failures=m.failures) for name,m in zip(NAMES,models)},
        residual_sigma_hz=sigma,wall_s=time.perf_counter()-began,
        accesses='public.npz and plans.npz only; no evaluator/paired branches/true gain',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save_json(dest/'initial.json',dict(fir=record,shuffled=shuffled,arx=ar,provisional=provisional))
    np.savez_compressed(dest/'online.npz',rolling=rolling,one_step=one_step,theta=theta,p=information,
                        contrast=contrast,detector=stats,calibration_residual=residual,width=width,update_ns=update_ns,
                        forecast_ns=forecast_ns,update_counts=update_counts,coefficient_norm=norm,kernel_gain_proxy=proxy,baseline=baseline)
    save_json(dest/'replay.json',metadata)
    if metadata['status']!='complete':raise ValueError('Recorded model failures; no successful qualification')


def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);began=time.perf_counter();record=provenance()
    record['protocol_sha256']=hashlib.sha256(Path('docs/research/008_M004_ONLINE_IDENTIFICATION_PROTOCOL.md').read_bytes()).hexdigest()
    record['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();save_json(args.output/'provenance.json',record)
    for folder in sorted(args.raw.glob('n*_r*')):
        run_trial(folder,args.output);print(folder.name,flush=True)
    hashes={str(f.relative_to(args.output)):hashlib.sha256(f.read_bytes()).hexdigest() for f in args.output.rglob('*') if f.is_file()}
    save_json(args.output/'seal.json',dict(status='complete',artifact_sha256=hashes,wall_s=time.perf_counter()-began))


if __name__=='__main__':main()
