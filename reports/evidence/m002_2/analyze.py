"""Frozen M002.2 analysis; no controller/model identification or action search."""
import csv
import json
from pathlib import Path
import sys
import time
import numpy as np
from neuromancer.reachability import NAMES,GAINS,REPLICATES,intervention_bank


def save_json(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def write_csv(path,rows):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def noise_summary(values):
    """Three independent noise replicates on axis1, not time-bin replication."""
    values=np.asarray(values)
    assert values.shape[:2]==(10,3)
    mean=values.mean(axis=1);sd=values.std(axis=1,ddof=1)
    width=4.3026527299*sd/np.sqrt(3)
    return dict(mean=mean.tolist(),sd=sd.tolist(),lower=(mean-width).tolist(),upper=(mean+width).tolist(),
                replicates=3,ci='pointwise95% Student-t, df2')


def hierarchy(values):
    values=np.asarray(values);assert values.shape[:2]==(10,3)
    shape=values.shape[2:];flat=values.reshape(10,3,-1)
    rng=np.random.default_rng(20261022);means=[]
    for _ in range(100):
        networks=rng.integers(0,10,(100,10));noise=rng.integers(0,3,(100,10,3))
        means.append(flat[networks[:,:,None],noise].mean(axis=(1,2)))
    samples=np.concatenate(means).reshape((10000,)+shape)
    return dict(mean=values.mean(axis=(0,1)).tolist(),lower=np.quantile(samples,.025,axis=0).tolist(),
                upper=np.quantile(samples,.975,axis=0).tolist(),seed=20261022,resamples=10000,
                ci='pointwise95% hierarchical percentile bootstrap')


def first_run(mask):
    mask=np.asarray(mask,dtype=bool)
    if len(mask)<3:return None
    where=np.flatnonzero(mask[:-2]&mask[1:-1]&mask[2:])
    return int(where[0]) if len(where) else None


def condition_readout(raw,baseline):
    """One scalar midpoint on noise5; balanced accuracy only on noise6/7."""
    blocks=raw[...,50:].reshape(10,3,2,12,5,50).mean(axis=-1)-baseline[:,:,None,None,None]
    pairs=((0,8),(3,4),(4,8))
    accuracy=np.empty((10,2,2,3));threshold=np.empty((10,2,3));orientation=np.empty_like(threshold)
    for j,(left,right) in enumerate(pairs):
        low=blocks[:,0,:,left].mean(axis=-1);high=blocks[:,0,:,right].mean(axis=-1)
        threshold[:,:,j]=(low+high)/2;orientation[:,:,j]=np.where(high>=low,1,-1)
        for r in range(2):
            a=orientation[:,:,j,None]*(blocks[:,r+1,:,left]-threshold[:,:,j,None])<0
            b=orientation[:,:,j,None]*(blocks[:,r+1,:,right]-threshold[:,:,j,None])>=0
            accuracy[:,r,:,j]=.5*(a.mean(axis=-1)+b.mean(axis=-1))
    network_mean=accuracy.mean(axis=1)
    indices=np.random.default_rng(20261022).integers(0,10,(10000,10))
    bootstrap=network_mean[indices].mean(axis=1)
    return dict(pairs=[[NAMES[a],NAMES[b]] for a,b in pairs],calibration_replicate=5,
        evaluation_replicates=[6,7],threshold_hz=threshold.tolist(),orientation=orientation.tolist(),
        accuracy_by_noise=accuracy.tolist(),network_accuracy=network_mean.tolist(),
        mean=network_mean.mean(axis=0).tolist(),lower=np.quantile(bootstrap,.025,axis=0).tolist(),
        upper=np.quantile(bootstrap,.975,axis=0).tolist(),
        inference='network bootstrap after averaging evaluation noise; blocks are repeated measures')


def objective_gate(late,noise,baseline):
    stats=noise_summary(late)
    rstar=.6*late[:,:,0,8].mean(axis=1)
    span=.8*rstar;high=.9*rstar
    reduced_lower=np.asarray(stats['lower'])[:,1,8]
    valid=((baseline>=1)&(baseline<=30)).all(axis=1)
    result=dict(reference_action='C120',scale_hz=rstar.tolist(),span_hz=span.tolist(),high_hz=high.tolist(),
        reduced_response_lower95_hz=reduced_lower.tolist(),minimum_span_hz=1,minimum_snr=2,scales={})
    for label,sigma in noise.items():
        sigma=np.sqrt((sigma**2).mean(axis=1))
        components=dict(minimum_span=span>=1,signal_to_noise=span>=2*sigma,
            reduced_headroom=high<=reduced_lower,baseline_valid=valid)
        passed=np.logical_and.reduce(list(components.values()))
        result['scales'][label]=dict(sigma_hz=sigma.tolist(),components={k:v.tolist() for k,v in components.items()},
            component_counts={k:int(v.sum()) for k,v in components.items()},network_pass=passed.tolist(),
            pass_count=int(passed.sum()),qualified=bool(passed.sum()>=8))
    result['selected_scale']=next((k for k in ('filtered100ms','epoch1s') if result['scales'][k]['qualified']),None)
    result['recommendation']='CONDITIONAL_CONFIRMATION' if result['selected_scale'] else 'HOLD'
    return result


def temporal_metrics(filtered_delta,late):
    records=[]
    for n in range(10):
        for g,gain in enumerate(GAINS):
            for a in (4,8):
                ref=float(late[n,:,g,a].mean());trace=filtered_delta[n,:,g,a].mean(axis=0)
                index=first_run(trace[:50]>=.5*ref) if ref>=.25 else None
                records.append(dict(network_id=n,gain=gain,action=NAMES[a],metric='static_t50',
                    time_s=None if index is None else (index+1)*.02,reference_response_hz=ref,
                    status='unresolved_or_censored' if index is None else 'crossing',resolution_s=.02))
            for a,zero_bin,peak_bins in ((9,26,25),(11,8,15)):
                cycles=filtered_delta[n,:,g,a].reshape(3,6,50)[:,1:].mean(axis=(0,1))
                peak=float(cycles[:peak_bins].max());index=None
                if peak>=.25:index=first_run(np.abs(cycles[zero_bin:])<=.2*peak)
                records.append(dict(network_id=n,gain=gain,action=NAMES[a],metric='recovery_t20',
                    time_s=None if index is None else (index+1)*.02,reference_response_hz=peak,
                    status='unresolved_or_censored' if index is None else 'crossing',resolution_s=.02))
    return records


def main(raw,output):
    began=time.perf_counter_ns();raw=Path(raw);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    complete=json.loads((raw/'summary.json').read_text())
    assert complete['status']=='complete' and len(complete['trials'])==30
    arrays={};trials=[];receipts=[]
    for n in range(10):
        for r,rep in enumerate(REPLICATES):
            folder=raw/f'network_{n}_replicate_{rep}'
            trial=json.loads((folder/'trial.json').read_text());assert trial['status']=='complete'
            trials.append(trial);receipts.extend(dict(network_id=n,replicate_id=rep,**item) for item in trial['receipt_ledger'])
            with np.load(folder/'numerical.npz',allow_pickle=False) as data:
                for key in data.files:
                    if key not in arrays:arrays[key]=np.empty((10,3)+data[key].shape,dtype=data[key].dtype)
                    arrays[key][n,r]=data[key]
    observed=arrays['observed_counts'].reshape(10,3,2,12,300,4,5)
    sector=observed[...,:4].sum(axis=-1)/.4
    raw_rate=sector.mean(axis=-1);filtered=arrays['filtered_sector_rates_hz'].mean(axis=-1)
    paired=raw_rate-raw_rate[:,:,:,0:1,:];filtered_delta=filtered-filtered[:,:,:,0:1,:]
    group_sizes=np.asarray(trials[0]['group_sizes'])
    group_rate=arrays['group_counts']/(group_sizes*.02)
    group_delta=group_rate-group_rate[:,:,:,0:1,:,:]
    np.testing.assert_allclose(group_rate[...,0],raw_rate,atol=1e-12,rtol=0)
    baseline_sector=arrays['baseline_counts'].reshape(10,3,400,4,5)[...,:4].sum(axis=-1)/.4
    baseline_raw=baseline_sector.mean(axis=-1);baseline=baseline_raw.mean(axis=-1)
    whole=paired.mean(axis=-1);late=paired[...,50:].mean(axis=-1)
    baseline_sigma=baseline_raw.std(axis=-1,ddof=1)
    sigma_filtered=filtered[:,:,0,0,50:].std(axis=-1,ddof=1)
    sigma_epoch=raw_rate[:,:,0,0,50:].reshape(10,3,5,50).mean(axis=-1).std(axis=-1,ddof=1)
    gate=objective_gate(late,dict(filtered100ms=sigma_filtered,epoch1s=sigma_epoch),baseline)
    dynamic_compare=np.stack([whole[:,:,:,9]-whole[:,:,:,3],whole[:,:,:,10]-whole[:,:,:,8],
                              whole[:,:,:,11]-whole[:,:,:,1]],axis=-1)
    phases=paired.reshape(10,3,2,12,6,50)[:,:,:,:,1:,:]
    pulse_recovery=phases[:,:,:,11,:,15:45].mean(axis=(-1,-2))
    periodic_recovery=phases[:,:,:,9,:,30:].mean(axis=(-1,-2))
    cycle_filtered=filtered_delta.reshape(10,3,2,12,6,50)[:,:,:,:,1:,:].mean(axis=-2)
    sector_delta=sector-sector[:,:,:,0:1,:,:]
    sector_phase=sector_delta.reshape(10,3,2,12,6,50,4)[:,:,:,:,1:,:,:]
    alternate=np.stack((sector_phase[:,:,:,10,:,:25,:].mean(axis=(-2,-3)),
                        sector_phase[:,:,:,10,:,25:,:].mean(axis=(-2,-3))),axis=-2)
    network_means=whole.mean(axis=1)
    selection=whole[:,0,:,1:].argmax(axis=-1)+1
    selected=np.take_along_axis(whole[:,1:,:,:],selection[:,None,:,None],axis=-1)[...,0]
    finite=dict(network_min_hz=network_means.min(axis=-1).tolist(),network_max_hz=network_means.max(axis=-1).tolist(),
        static_max_hz=network_means[:,:,:9].max(axis=-1).tolist(),dynamic_max_hz=network_means[:,:,9:].max(axis=-1).tolist(),
        noise5_selected_actions=[[NAMES[j] for j in row] for row in selection],
        selected_noise6_7_hz=selected.tolist(),inference='finite-bank maxima are optimistic; not the mathematical reachable set')
    summaries=dict(whole=hierarchy(whole),late_static=hierarchy(late),network_whole=noise_summary(whole),
        network_late=noise_summary(late),group_response=hierarchy(group_delta.mean(axis=-2)),
        sector_response=hierarchy(sector_delta.mean(axis=-2)),filtered_response=hierarchy(filtered_delta.mean(axis=-1)),
        dynamic_minus_charge_matched_static=hierarchy(dynamic_compare),
        pulse_recovery=hierarchy(pulse_recovery),periodic_recovery=hierarchy(periodic_recovery),
        dynamic_cycle_filtered=hierarchy(cycle_filtered[:,:,:,9:,:]),alternate_sector_phase=hierarchy(alternate),
        gain06_minus_gain1=hierarchy(whole[:,:,1,:]-whole[:,:,0,:]))
    comparisons=dict(action_names=NAMES,gains=GAINS,replicate_ids=REPLICATES,networks=10,
        noise_replicates=3,completed_branches=len(receipts),constraint_violations=sum(r['constraint_violations'] for r in receipts),
        group_names=trials[0]['group_names'],group_sizes=group_sizes.tolist(),summaries=summaries,
        finite_bank=finite,objective_gate=gate,condition_readout=condition_readout(raw_rate,baseline),
        baseline=dict(mean_hz=baseline.tolist(),raw20ms_sigma_hz=baseline_sigma.tolist(),
                      filtered100ms_sigma_hz=sigma_filtered.tolist(),epoch1s_sigma_hz=sigma_epoch.tolist()),
        raw_wall_ns=complete['wall_ns'],analysis_compute_ns=time.perf_counter_ns()-began)
    rows=[];network_rows=[];sector_rows=[]
    for n in range(10):
        for r,rep in enumerate(REPLICATES):
            for g,gain in enumerate(GAINS):
                for a,name in enumerate(NAMES):
                    row=dict(network_id=n,replicate_id=rep,gain=gain,action=name,
                        baseline_hz=float(baseline[n,r]),absolute_rate_hz=float(raw_rate[n,r,g,a].mean()),
                        whole_response_hz=float(whole[n,r,g,a]),late_response_hz=float(late[n,r,g,a]),
                        filtered_response_hz=float(filtered_delta[n,r,g,a].mean()))
                    for j,label in enumerate(trials[0]['group_names']):row[label+'_response_hz']=float(group_delta[n,r,g,a,:,j].mean())
                    rows.append(row)
                    for j in range(4):sector_rows.append(dict(network_id=n,replicate_id=rep,gain=gain,action=name,sector=j,
                        absolute_rate_hz=float(sector[n,r,g,a,:,j].mean()),
                        paired_response_hz=float(sector_delta[n,r,g,a,:,j].mean())))
        for g,gain in enumerate(GAINS):
            for a,name in enumerate(NAMES):
                row=dict(network_id=n,gain=gain,action=name)
                for label in ('whole','late'):
                    for key in ('mean','sd','lower','upper'):
                        row[label+'_'+key+'_hz']=summaries['network_'+label][key][n][g][a]
                network_rows.append(row)
    assert len(rows)==720 and len(network_rows)==240 and len(sector_rows)==2880
    assert comparisons['constraint_violations']==0
    save_json(output/'comparison.json',comparisons);save_json(output/'trial_provenance.json',trials)
    save_json(output/'delivered_actions.json',receipts);save_json(output/'temporal_metrics.json',temporal_metrics(filtered_delta,late))
    write_csv(output/'all_trials.csv',rows);write_csv(output/'network_summary.csv',network_rows)
    write_csv(output/'sector_trials.csv',sector_rows)
    np.savez_compressed(output/'reachability_data.npz',**arrays,raw_rate_hz=raw_rate,paired_response_hz=paired,
        filtered_response_hz=filtered_delta,whole_response_hz=whole,late_response_hz=late)
    print(json.dumps(dict(branches=len(rows),objective=gate['recommendation'],scale=gate['selected_scale']),indent=2))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
