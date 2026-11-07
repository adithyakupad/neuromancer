"""Frozen M002.3 network-level analysis; no simulation or action selection."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

T4=2.7764451051977987
REPS=(8,9,10,11,12)
NAMES=('S','C120','L','H')
GAINS=(1.,.6)


def clean(value):
    if isinstance(value,np.ndarray):return clean(value.tolist())
    if isinstance(value,np.generic):return clean(value.item())
    if isinstance(value,float) and not np.isfinite(value):return None
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    return value


def save(path,value):path.write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n')


def csv_write(path,rows):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(clean(rows))


def ci(values):
    x=np.asarray(values,dtype=float)
    if not np.isfinite(x).all():return dict(mean=None,lower=None,upper=None)
    mean=x.mean(axis=0);half=T4*x.std(axis=0,ddof=1)/np.sqrt(5)
    return clean(dict(mean=mean,lower=mean-half,upper=mean+half))


def network_bootstrap(values):
    x=np.asarray(values,dtype=float)
    assert x.shape[0]==10
    if not np.isfinite(x).all():return dict(mean=None,lower=None,upper=None)
    draws=np.random.default_rng(20261023).integers(0,10,(10000,10))
    samples=x[draws].mean(axis=1)
    return clean(dict(mean=x.mean(axis=0),lower=np.quantile(samples,.025,axis=0),upper=np.quantile(samples,.975,axis=0)))


def gate(baseline,sector,span,sigma,margin,errors,valid,stable):
    components=dict(baseline_valid=bool(np.all((baseline>=1)&(baseline<=30)) and np.all(sector<100) and stable),
        minimum_span=bool(np.isfinite(span).all() and span.mean()>=1),
        noise=bool(np.isfinite(span).all() and span.mean()>=2*np.sqrt(np.mean(sigma**2))),
        headroom=bool(np.isfinite(margin).all() and margin.mean()-T4*margin.std(ddof=1)/np.sqrt(5)>=0),
        calibration=bool(np.all(valid)))
    for gi,gain in enumerate(GAINS):
        for ti,target in enumerate(('L','H')):
            x=errors[:,gi,ti]
            components[f'error_g{gain}_{target}']=bool(np.all(valid) and np.isfinite(x).all() and x.mean()<=.25)
    return dict(components=components,qualified=all(components.values()))


def main(raw,output):
    began=time.perf_counter_ns();raw=Path(raw);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    trials=[];arrays={};cal=[];branches=[];network=[]
    for n in range(10):
        per=[]
        for ri,rep in enumerate(REPS):
            folder=raw/f'network_{n}_replicate_{rep}'
            trial=json.loads((folder/'trial.json').read_text());assert trial['status']=='complete'
            trials.append(trial)
            with np.load(folder/'numerical.npz',allow_pickle=False) as archive:
                data={key:archive[key] for key in archive.files}
            for key,value in data.items():
                if key not in arrays:arrays[key]=np.empty((10,5,*value.shape),dtype=value.dtype)
                arrays[key][n,ri]=value
            pc=data['prefix_counts'].reshape(2550,4,5)[:,:,:4]
            baseline_sector=pc[350:750].sum(axis=(0,2))/(20*8)
            oc=data['observed_counts'].reshape(2,4,300,4,5)[:,:,:,:,:4]
            rates=oc.sum(axis=(-1,-2))/1.6
            late=rates[:,:,50:].mean(axis=-1);whole=rates.mean(axis=-1)
            target=np.asarray(trial['calibration']['targets_hz']);span=trial['calibration']['span_hz']
            valid=trial['calibration']['valid']
            error=late[:,2:]-target[None,:]
            norm=np.abs(error)/span if valid and span>0 else np.full((2,2),np.nan)
            sigma=rates[0,0,50:].reshape(5,50).mean(axis=1).std(ddof=1)
            fast=data['filtered_sector_rates_hz'][0,0,50:].mean(axis=-1).std(ddof=1)
            margin=late[1,1]-late[1,0]-(target[1]-trial['calibration']['baseline_hz'])
            stable=bool(np.isfinite(data['filtered_sector_rates_hz']).all() and np.all(oc.sum(axis=(2,4))/(20*6)<100))
            row=dict(network_id=n,replicate_id=rep,baseline_hz=trial['calibration']['baseline_hz'],
                low_target_hz=target[0],high_target_hz=target[1],span_hz=span,standalone_sd_1s_hz=sigma,
                standalone_sd_100ms_hz=fast,headroom_margin_hz=margin,calibration_valid=valid,
                invalid_reason=trial['calibration']['reason'],q_low_pA=(trial['calibration']['lookup_pA'] or [None,None])[0],
                q_high_pA=(trial['calibration']['lookup_pA'] or [None,None])[1])
            for j,h in enumerate(trial['calibration']['h_hz']):row[f'h_{j*30}_hz']=h
            cal.append(row)
            for gi,gain in enumerate(GAINS):
                for ai,name in enumerate(NAMES):
                    ledger=trial['receipt_ledger'][gi*4+ai]
                    assert ledger['gain']==gain
                    entry=dict(network_id=n,replicate_id=rep,condition=name,
                        whole_rate_hz=whole[gi,ai],late_rate_hz=late[gi,ai],paired_late_response_hz=late[gi,ai]-late[gi,0],
                        target_hz=target[ai-2] if ai>=2 else None,
                        signed_error_hz=error[gi,ai-2] if ai>=2 else None,
                        absolute_error_hz=abs(error[gi,ai-2]) if ai>=2 else None,
                        normalized_absolute_error=norm[gi,ai-2] if ai>=2 else None,**ledger)
                    branches.append(entry)
            per.append(dict(base=baseline_sector.mean(),sector=baseline_sector,span=span,sigma=sigma,fast=fast,
                margin=margin,error=norm,valid=valid,stable=stable,late=late,target=target,signed_error=error))
        take=lambda key:np.asarray([p[key] for p in per])
        decision=gate(take('base'),take('sector'),take('span'),take('sigma'),take('margin'),take('error'),take('valid'),bool(take('stable').all()))
        result=dict(network_id=n,**decision,baseline=ci(take('base')),targets=ci(take('target')),span=ci(take('span')),
            sigma_1s_rms=float(np.sqrt(np.mean(take('sigma')**2))),sigma_100ms_rms=float(np.sqrt(np.mean(take('fast')**2))),
            reduced_headroom=ci(take('margin')),late_rates=ci(take('late')),normalized_absolute_error=ci(take('error')),
            signed_error=ci(take('signed_error')),calibration_failures=int((~take('valid')).sum()))
        network.append(result)
    arrays['raw_rate_hz']=arrays['observed_counts'].reshape(10,5,2,4,300,4,5)[:,:,:,:,:,:,:4].sum(axis=(-1,-2))/1.6
    np.savez_compressed(output/'calibration_data.npz',**arrays)
    csv_write(output/'calibration_trials.csv',cal);csv_write(output/'confirmation_trials.csv',branches)
    rows=[]
    for item in network:
        row=dict(network_id=item['network_id'],qualified=item['qualified'],**item['components'],
            baseline_hz=item['baseline']['mean'],low_target_hz=item['targets']['mean'][0],high_target_hz=item['targets']['mean'][1],
            span_hz=item['span']['mean'],sigma_1s_hz=item['sigma_1s_rms'],headroom_mean_hz=item['reduced_headroom']['mean'],
            headroom_lower_hz=item['reduced_headroom']['lower'],calibration_failures=item['calibration_failures'])
        for gi,gain in enumerate(GAINS):
            for ti,target in enumerate(('L','H')):
                row[f'normalized_error_g{gain}_{target}']=item['normalized_absolute_error']['mean'][gi][ti] if item['normalized_absolute_error']['mean'] is not None else None
        rows.append(row)
    csv_write(output/'network_qualification.csv',rows)
    qualified=sum(n['qualified'] for n in network);z=1.959963984540054;p=qualified/10
    center=(p+z*z/20)/(1+z*z/10);half=z*np.sqrt(p*(1-p)/10+z*z/400)/(1+z*z/10)
    summary=json.loads((raw/'summary.json').read_text())
    comparison=dict(completed_trials=len(trials),completed_branches=len(branches),execution_complete=summary['status']=='complete',
        scientific_qualification='PASS' if qualified>=8 else 'HOLD',qualified_networks=qualified,
        descriptive_wilson95=[center-half,center+half],
        component_counts={k:sum(n['components'][k] for n in network) for k in network[0]['components']},networks=network,
        aggregate=dict(span_hz=network_bootstrap([n['span']['mean'] for n in network]),
            headroom_hz=network_bootstrap([n['reduced_headroom']['mean'] for n in network]),
            normalized_error=network_bootstrap([n['normalized_absolute_error']['mean'] if n['normalized_absolute_error']['mean'] is not None else [[np.nan]*2]*2 for n in network]),
            late_rates_hz=network_bootstrap([n['late_rates']['mean'] for n in network])),
        calibration_invalid_count=sum(not t['calibration']['valid'] for t in trials),
        constraint_violations=sum(b['constraint_violations'] for b in branches),
        scientific_wall_s=summary['wall_ns']/1e9,
        peak_worker_rss_bytes=max(t['peak_rss_bytes'] for t in trials),
        worker_wall_s=ci(np.array([sum(t['total_wall_ns']/1e9 for t in trials if t['replicate_id']==r)/10 for r in REPS])),
        initialization_ms=[t['engine']['initialization_ns']/1e6 for t in trials],
        neural_wall_s=sum(b['neural_ns'] for b in branches)/1e9,
        observation_wall_s=sum(b['observation_ns'] for b in branches)/1e9)
    save(output/'comparison.json',comparison);save(output/'trial_provenance.json',trials)
    save(output/'raw_summary.json',summary);save(output/'raw_provenance.json',json.loads((raw/'provenance.json').read_text()))
    save(output/'analysis_lineage.json',dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        wall_s=(time.perf_counter_ns()-began)/1e9,counts_shape=arrays['observed_counts'].shape,
        prefix_shape=arrays['prefix_counts'].shape,replicate_ids=REPS,network_ids=list(range(10))))
    print(json.dumps(clean({k:v for k,v in comparison.items() if k not in ('networks','initialization_ms')}),indent=2))


if __name__=='__main__':main(*sys.argv[1:])
