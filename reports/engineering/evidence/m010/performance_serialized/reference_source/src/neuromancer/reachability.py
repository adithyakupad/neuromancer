"""Preregistered M002.2 open-loop probes; original neural instrument is unchanged."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gc
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import resource
import sys
import time
import numpy as np
from .authority_diagnosis import evaluator_groups
from .diagnostic import provenance,run_hold,schedule
from .substrate import Config

NAMES=('S','D6','D15','D30','D60','C30','C60','C90','C120',
       'PERIODIC','ALTERNATE','PULSE')
GAINS=(1.,.6)
REPLICATES=(5,6,7)
BIN_US=20_000
EXPECTED_EXPOSURE=(0,144,360,720,1437.6,360,718.8,1076.4,1432.8,720,1432.8,144)


def intervention_bank():
    desired=np.zeros((12,300,4))
    for index,value in enumerate((6,15,30,60),1):desired[index]=value
    for index,value in enumerate((30,60,90,120),5):desired[index,:,::2]=value
    for tick in range(300):
        phase=tick%50
        desired[9,tick]=60 if phase<25 else 0
        desired[10,tick,[0,2] if phase<25 else [1,3]]=120
        if phase<5:desired[11,tick,::2]=120
    actual=np.empty_like(desired)
    for action in range(12):
        prior=np.zeros(4)
        for tick in range(300):
            actual[action,tick]=np.clip(desired[action,tick],prior-30,prior+30)
            prior=actual[action,tick]
        audit=audit_actions(actual[action])
        assert audit['constraint_violations']==0
        assert abs(audit['total_exposure_pA_s']-EXPECTED_EXPOSURE[action])<1e-9
    return desired,actual


def audit_actions(rows):
    rows=np.asarray(rows,dtype=float)
    if rows.shape!=(300,4) or not np.isfinite(rows).all():raise ValueError('Expected finite 300x4 pA schedule')
    slew=np.diff(np.vstack([np.zeros(4),rows]),axis=0)
    violations=int(((rows<0)|(rows>120)).sum()+(rows.sum(axis=1)>240).sum()+(np.abs(slew)>30).sum())
    exposure=float(rows.sum()*.02)
    return dict(constraint_violations=violations,total_exposure_pA_s=exposure,
        per_channel_exposure_pA_s=(rows.sum(axis=0)*.02).tolist(),
        aggregate_injected_charge_pC=50*exposure,maximum_total_current_pA=float(rows.sum(axis=1).max()),
        maximum_slew_pA=float(np.abs(slew).max()),endpoint_pA=rows[-1].tolist())


def state_hashes(engine):
    return {key:hashlib.sha256(np.asarray(getattr(engine.group,key)).tobytes()).hexdigest()
            for key in ('v','I_E','I_I','eta','lastspike','not_refractory')}


def run_trial(network_id,replicate_id,output):
    import brian2 as b
    from ._brian import BrianEngine
    folder=Path(output)/f'network_{network_id}_replicate_{replicate_id}'
    folder.mkdir(exist_ok=False)
    began=time.perf_counter_ns();engine=None
    try:
        config=Config(network_id=network_id,replicate_id=replicate_id,
            trial_id=f'reach-n{network_id}-r{replicate_id}',retain_spikes=True)
        engine=BrianEngine(config)
        _,burn_ns=run_hold(engine,5,0)
        baseline,baseline_ns=run_hold(engine,10,0)
        baseline_counts=np.array([r.observation.counts for r in baseline[100:]],dtype=np.int32)
        baseline_rate=float(np.mean([r.observation.sector_rate_hz for r in baseline[100:]]))
        engine.save('baseline');checkpoint=state_hashes(engine)
        prefix_events=len(engine.monitor.i);prefix_counts=np.asarray(engine.monitor.count).copy()
        groups=evaluator_groups(engine.parameters);labels=list(groups)
        group_masks=[np.isin(np.arange(1000),ids) for ids in groups.values()]
        group_counts=np.empty((2,12,300,len(groups)),dtype=np.int32)
        neuron_counts=np.empty((2,12,1000),dtype=np.int32)
        observed_counts=np.empty((2,12,300,20),dtype=np.int32)
        filtered=np.empty((2,12,300,4))
        delivered=np.empty((2,12,300,4))
        desired,bank=intervention_bank();noise_id=None;ledger=[];timings=[]
        for g,gain in enumerate(GAINS):
            for a,name in enumerate(NAMES):
                engine.restore('baseline')
                assert state_hashes(engine)==checkpoint and engine.time_us==15_000_000
                assert not np.any(engine.previous)
                engine.group.gain=gain
                start=time.perf_counter_ns()
                result=engine.run_commands(schedule(engine,bank[a]))
                elapsed=time.perf_counter_ns()-start
                extracted=time.perf_counter_ns()
                ids=np.asarray(engine.monitor.i[prefix_events:],dtype=np.int64)
                times=np.rint(np.asarray(engine.monitor.t[prefix_events:]/b.us)).astype(np.int64)
                assert np.all((times>=15_000_000)&(times<21_000_000))
                bins=(times-15_000_000)//BIN_US
                neuron_counts[g,a]=np.bincount(ids,minlength=1000)
                np.testing.assert_array_equal(neuron_counts[g,a],np.asarray(engine.monitor.count)-prefix_counts)
                for j,mask in enumerate(group_masks):
                    group_counts[g,a,:,j]=np.bincount(bins[mask[ids]],minlength=300)
                observed_counts[g,a]=[r.observation.counts for r in result]
                pooled=observed_counts[g,a].reshape(300,4,5)[:,:,:4].sum(axis=(1,2))
                np.testing.assert_array_equal(pooled,group_counts[g,a,:,labels.index('observed_E')])
                for j,members in enumerate(groups.values()):
                    assert group_counts[g,a,:,j].sum()==neuron_counts[g,a,members].sum()
                filtered[g,a]=[r.observation.filtered_sector_rate_hz for r in result]
                assert np.isfinite(filtered[g,a]).all()
                for tick,r in enumerate(result):
                    assert r.observation.start_us==15_000_000+tick*BIN_US
                    assert r.observation.available_us==r.observation.stop_us==15_020_000+tick*BIN_US
                    assert all(r.observation.valid) and r.receipt.requested_current_pA==r.receipt.delivered_current_pA
                delivered[g,a]=[r.receipt.delivered_current_pA for r in result]
                np.testing.assert_array_equal(delivered[g,a],bank[a])
                audit=audit_actions(delivered[g,a]);assert audit['constraint_violations']==0
                current_noise=dict(engine.noise_hashes)
                if noise_id is None:noise_id=current_noise
                else:assert current_noise==noise_id
                receipt=dict(gain=gain,action=name,start_us=15_000_000,stop_us=21_000_000,
                    effective_drive_exposure_pA_s=gain*audit['total_exposure_pA_s'],**audit)
                timing=dict(gain=gain,action=name,simulation_call_ns=elapsed,
                    neural_ns=sum(r.neural_wall_ns for r in result),
                    observation_ns=sum(r.observation_wall_ns for r in result),
                    extraction_ns=time.perf_counter_ns()-extracted)
                ledger.append(receipt);timings.append(timing)
                with (folder/'conditions.jsonl').open('a') as file:
                    file.write(json.dumps(dict(receipt=receipt,timing=timing),allow_nan=False)+'\n')
        np.testing.assert_array_equal(neuron_counts[0,0],neuron_counts[1,0])
        np.testing.assert_array_equal(observed_counts[0,0],observed_counts[1,0])
        np.testing.assert_array_equal(filtered[0,0],filtered[1,0])
        np.savez_compressed(folder/'numerical.npz',group_counts=group_counts,neuron_counts=neuron_counts,
            observed_counts=observed_counts,filtered_sector_rates_hz=filtered,delivered_current_pA=delivered,
            desired_target_pA=desired,baseline_counts=baseline_counts,
            stimulation=engine.parameters['stimulation'],recording=engine.parameters['recording'],
            bin_start_us=np.arange(15_000_000,21_000_000,BIN_US))
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        report=dict(status='complete',network_id=network_id,replicate_id=replicate_id,
            baseline_observed_E_hz=baseline_rate,checkpoint_hashes=checkpoint,group_names=labels,
            group_sizes=[len(v) for v in groups.values()],engine=engine.provenance(),
            receipt_ledger=ledger,timings=timings,burn_call_ns=burn_ns,baseline_call_ns=baseline_ns,
            peak_rss_bytes=int(rss),total_wall_ns=time.perf_counter_ns()-began)
        (folder/'trial.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        return dict(network_id=network_id,replicate_id=replicate_id,status='complete',wall_ns=report['total_wall_ns'])
    except Exception as error:
        failure=dict(network_id=network_id,replicate_id=replicate_id,status='failed',error=f'{type(error).__name__}: {error}')
        (folder/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        return failure
    finally:
        if engine is not None:engine.close()
        del engine;gc.collect()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault('MPLCONFIGDIR',str(args.output.resolve()/'.mpl-cache'))
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
    root=Path(__file__).resolve().parents[2]
    prereg=root/'reports/evidence/m002_2/PREREGISTRATION.md'
    record=provenance();record['preregistration_files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(prereg.parent.glob('PREREGISTRATION*.md'))}
    record.update(preregistration_sha256=hashlib.sha256(prereg.read_bytes()).hexdigest(),
        design=dict(network_ids=list(range(10)),replicate_ids=REPLICATES,gains=GAINS,action_names=NAMES,
                    duration_us=6_000_000,baseline_stop_us=15_000_000,workers=3,simulated_seconds=4770))
    (args.output/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    desired,actual=intervention_bank()
    (args.output/'intervention_bank.json').write_text(json.dumps({name:dict(desired_target_pA=desired[a].tolist(),
        delivered_schedule_pA=actual[a].tolist(),bin_start_us=list(range(15_000_000,21_000_000,BIN_US)),
        **audit_actions(actual[a])) for a,name in enumerate(NAMES)},indent=2)+'\n')
    began=time.perf_counter_ns();results=[]
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        futures=[pool.submit(run_trial,n,r,str(args.output)) for n in range(10) for r in REPLICATES]
        for future in as_completed(futures):
            result=future.result();results.append(result);print(f'{len(results)}/30 {result}',flush=True)
            (args.output/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
    hashes={str(p.relative_to(args.output)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.output.rglob('*')) if p.is_file() and '.mpl-cache' not in p.parts}
    summary=dict(status='complete' if all(x['status']=='complete' for x in results) else 'partial',
        trials=sorted(results,key=lambda x:(x['network_id'],x['replicate_id'])),
        wall_ns=time.perf_counter_ns()-began,artifact_sha256=hashes)
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if summary['status']!='complete':raise SystemExit('Incomplete fixed cohort; see retained failures')


if __name__=='__main__':main()
