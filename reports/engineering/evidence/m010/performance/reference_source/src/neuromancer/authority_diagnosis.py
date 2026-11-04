"""M002.1 preregistered evaluator-only allocation bank. No neural model changes."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gc
import hashlib
from itertools import combinations
import json
import multiprocessing as mp
import os
from pathlib import Path
import resource
import sys
import time
import numpy as np
from .substrate import Config
from .diagnostic import provenance, run_hold, schedule

NAMES = ('S','D','C01','C02','C03','C12','C13','C23')
GAINS = (.6, 1.)
TARGETS = np.array([(0,0,0,0), (60,60,60,60)] +
                   [tuple(120 if j in pair else 0 for j in range(4))
                    for pair in combinations(range(4),2)], dtype=float)


def action_schedule(target):
    rows=np.empty((250,4),dtype=float)
    previous=np.zeros(4)
    for tick in range(250):
        rows[tick]=np.clip(target,previous-30,previous+30)
        previous=rows[tick]
    return rows


def action_audit(rows):
    rows=np.asarray(rows)
    if rows.shape!=(250,4) or not np.all(np.isfinite(rows)):
        raise ValueError('Expected a finite 250 by 4 current schedule')
    slew=np.diff(np.vstack([np.zeros(4),rows]),axis=0)
    violations=int(np.sum((rows<0)|(rows>120))+np.sum(rows.sum(axis=1)>240)
                   +np.sum(np.abs(slew)>30))
    return dict(constraint_violations=violations,
        total_exposure_pA_s=float(rows.sum()*.02),
        per_channel_exposure_pA_s=(rows.sum(axis=0)*.02).tolist(),
        aggregate_injected_charge_pC=float(50*rows.sum()*.02),
        maximum_total_current_pA=float(rows.sum(axis=1).max()),
        maximum_slew_pA=float(np.abs(slew).max()),
        post_ramp_exposure_pA_s=float(rows[3:].sum()*.02))


def evaluator_groups(parameters):
    stimulation=parameters['stimulation']
    recording=parameters['recording'].reshape(4,5,5)
    fixed=np.setdiff1d(np.arange(800),stimulation.ravel())
    groups={'observed_E':recording[:,:4,:].ravel(), 'fixed_unstim_E':fixed,
            'all_E':np.arange(800), 'all_I':np.arange(800,1000)}
    for j in range(4):
        groups[f'stim_channel_{j}']=stimulation[j]
        groups[f'observed_sector_{j}']=recording[j,:4,:].ravel()
        groups[f'fixed_unstim_sector_{j}']=np.intersect1d(fixed,np.arange(j*200,(j+1)*200))
        groups[f'E_sector_{j}']=np.arange(j*200,(j+1)*200)
        groups[f'I_sector_{j}']=np.arange(800+j*50,850+j*50)
    return groups


def _rss():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform=='darwin' else value*1024)


def run_trial(network_id,replicate_id,output):
    import brian2 as b
    from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
    from ._brian import BrianEngine
    folder=Path(output)/f'network_{network_id}_replicate_{replicate_id}'
    folder.mkdir(exist_ok=False)
    began=time.perf_counter_ns()
    engine=None
    try:
        config=Config(network_id=network_id,replicate_id=replicate_id,
                      trial_id=f'n{network_id}-r{replicate_id}')
        engine=BrianEngine(config)
        _,burn_ns=run_hold(engine,5,0)
        baseline,baseline_ns=run_hold(engine,10,0)
        baseline_rate=float(np.mean([x.observation.sector_rate_hz for x in baseline[100:]]))
        trace=b.StateMonitor(engine.group,['I_E','I_I'],record=True,dt=.02*b.second,
            when='end',codeobj_class=NumpyCodeObject)
        engine.net.add(trace)
        engine.save('common_baseline')
        checkpoint_count=np.asarray(engine.monitor.count).copy()
        checkpoint_hashes={key:hashlib.sha256(np.asarray(getattr(engine.group,key)).tobytes()).hexdigest()
                           for key in ['v','I_E','I_I','eta','lastspike','not_refractory']}
        groups=evaluator_groups(engine.parameters)
        labels=list(groups)
        spikes=np.empty((2,8,1000),dtype=np.int32)
        currents=np.empty((2,8,1000,2),dtype=float)
        observed_counts=np.empty((2,8,250,20),dtype=np.int32)
        sector_rates=np.empty((2,8,250,4),dtype=float)
        filtered_rates=np.empty_like(sector_rates)
        current_trace=np.empty((2,8,250,len(groups),2),dtype=float)
        delivered=np.empty((2,8,250,4),dtype=float)
        receipts=[]
        timings=[]
        noise_id=None
        schedules=[action_schedule(t) for t in TARGETS]
        for g,gain in enumerate(GAINS):
            for a,name in enumerate(NAMES):
                engine.restore('common_baseline')
                for key,value in checkpoint_hashes.items():
                    assert hashlib.sha256(np.asarray(getattr(engine.group,key)).tobytes()).hexdigest()==value
                assert engine.time_us==15_000_000 and np.all(engine.previous==0)
                engine.group.gain=gain
                t0=time.perf_counter_ns()
                result=engine.run_commands(schedule(engine,schedules[a]))
                elapsed=time.perf_counter_ns()-t0
                analysis_start=time.perf_counter_ns()
                spikes[g,a]=np.asarray(engine.monitor.count)-checkpoint_count
                assert np.all(spikes[g,a]>=0)
                observed_counts[g,a]=[x.observation.counts for x in result]
                sector_rates[g,a]=[x.observation.sector_rate_hz for x in result]
                filtered_rates[g,a]=[x.observation.filtered_sector_rate_hz for x in result]
                delivered[g,a]=[x.receipt.delivered_current_pA for x in result]
                np.testing.assert_array_equal(delivered[g,a],schedules[a])
                audit=action_audit(delivered[g,a]);assert audit['constraint_violations']==0
                times=np.rint(np.asarray(trace.t/b.us)).astype(np.int64)
                np.testing.assert_array_equal(times,np.arange(15_000_000,20_000_000,20000))
                neural_currents=np.stack((trace.I_E/b.pA,trace.I_I/b.pA),axis=-1)
                assert np.all(np.isfinite(neural_currents))
                currents[g,a]=neural_currents.mean(axis=1)
                for j,members in enumerate(groups.values()):
                    current_trace[g,a,:,j]=neural_currents[members].mean(axis=0)
                counts=spikes[g,a]
                np.testing.assert_allclose(sector_rates[g,a].mean(),counts[groups['observed_E']].mean()/5,
                                           rtol=0,atol=1e-12)
                this_noise=dict(engine.noise_hashes)
                if noise_id is None:noise_id=this_noise
                else:assert this_noise==noise_id
                receipts.append(dict(gain=gain,action=name,requested_schedule_id=name,
                    delivered_schedule_id=f'{network_id}:{replicate_id}:{gain}:{name}',
                    start_us=15_000_000,stop_us=20_000_000,available_us=20_000_000,
                    effective_drive_exposure_pA_s=gain*audit['total_exposure_pA_s'],**audit))
                timings.append(dict(gain=gain,action=name,simulation_call_ns=elapsed,
                    neural_ns=sum(x.neural_wall_ns for x in result),
                    observation_ns=sum(x.observation_wall_ns for x in result),
                    extraction_analysis_ns=time.perf_counter_ns()-analysis_start))
                with (folder/'conditions.jsonl').open('a') as log:
                    log.write(json.dumps(dict(receipt=receipts[-1],timing=timings[-1],
                        observed_E_hz=float(sector_rates[g,a].mean()),
                        fixed_unstim_E_hz=float(counts[groups['fixed_unstim_E']].mean()/5),
                        inhibitory_hz=float(counts[groups['all_I']].mean()/5)),allow_nan=False)+'\n')
        np.testing.assert_array_equal(spikes[0,0],spikes[1,0])
        np.testing.assert_array_equal(currents[0,0],currents[1,0])
        # Historical replicate-zero check is fixed before this run.
        if replicate_id==0:
            old=Path(__file__).resolve().parents[2]/'reports/evidence/m002/authority'/f'network_{network_id}.json'
            expected=json.loads(old.read_text())
            assert abs(baseline_rate-expected['baseline_recorded_E_hz'])<1e-12
            for g,key in [(0,'contrast_g06_hz'),(1,'contrast_g1_hz')]:
                delta=(spikes[g,1,groups['observed_E']]-spikes[g,0,groups['observed_E']]).mean()/5
                assert abs(delta-expected[key])<1e-12
        np.savez_compressed(folder/'numerical.npz',spike_counts=spikes,
            mean_current_pA=currents,observed_counts=observed_counts,
            sector_rates_hz=sector_rates,filtered_sector_rates_hz=filtered_rates,
            group_current_trace_pA=current_trace,delivered_current_pA=delivered,
            bin_start_us=np.arange(15_000_000,20_000_000,20000),
            stimulation=engine.parameters['stimulation'],recording=engine.parameters['recording'])
        report=dict(network_id=network_id,replicate_id=replicate_id,baseline_observed_E_hz=baseline_rate,
            checkpoint_hashes=checkpoint_hashes,group_names=labels,
            receipt_ledger=receipts,timings=timings,burn_call_ns=burn_ns,baseline_call_ns=baseline_ns,
            engine=engine.provenance(),peak_rss_bytes=_rss(),status='complete',
            total_wall_ns=time.perf_counter_ns()-began)
        (folder/'trial.json').write_text(json.dumps(report,indent=2)+'\n')
        return dict(network_id=network_id,replicate_id=replicate_id,status='complete',
                    wall_ns=report['total_wall_ns'])
    except Exception as error:
        failure=dict(network_id=network_id,replicate_id=replicate_id,status='failed',
                     error=f'{type(error).__name__}: {error}')
        (folder/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        return failure
    finally:
        if engine is not None:engine.close()
        del engine;gc.collect()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ.setdefault('MPLCONFIGDIR',str(args.output.resolve()/'.mpl-cache'))
    os.environ['OPENBLAS_NUM_THREADS']='1'
    os.environ['OMP_NUM_THREADS']='1'
    root=Path(__file__).resolve().parents[2]
    prereg=root/'reports/evidence/m002_1/PREREGISTRATION.md'
    record=provenance()
    record.update(preregistration_sha256=hashlib.sha256(prereg.read_bytes()).hexdigest(),
        design=dict(network_ids=list(range(10)),replicate_ids=list(range(5)),gains=GAINS,
                    action_names=NAMES,targets_pA=TARGETS.tolist(),workers=3))
    (args.output/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    bank={name:dict(target_pA=target.tolist(),schedule_pA=action_schedule(target).tolist(),
                   bin_start_us=list(range(15_000_000,20_000_000,20000)),
                   **action_audit(action_schedule(target))) for name,target in zip(NAMES,TARGETS)}
    (args.output/'intervention_bank.json').write_text(json.dumps(bank,indent=2)+'\n')
    began=time.perf_counter_ns();results=[]
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        futures=[pool.submit(run_trial,n,r,str(args.output)) for n in range(10) for r in range(5)]
        for future in as_completed(futures):
            result=future.result();results.append(result)
            print(f"{len(results)}/50 {result}",flush=True)
            (args.output/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
    hashes={str(p.relative_to(args.output)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(args.output.rglob('*')) if p.is_file() and '.mpl-cache' not in p.parts}
    summary=dict(status='complete' if all(x['status']=='complete' for x in results) else 'partial',
        trials=sorted(results,key=lambda x:(x['network_id'],x['replicate_id'])),
        wall_ns=time.perf_counter_ns()-began,artifact_sha256=hashes)
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if summary['status']!='complete':raise SystemExit('Some preregistered trials failed; see retained records')


if __name__=='__main__':main()
