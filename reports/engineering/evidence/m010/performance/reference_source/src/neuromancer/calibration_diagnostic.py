"""Fixed M002.3 evaluator: gains/private state never enter the calibration API."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed,TimeoutError
from dataclasses import asdict
import gc
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import time
import numpy as np
from .calibration import fit,prefix_schedule,ramp
from .diagnostic import provenance,schedule,peak_rss_bytes
from .reachability import audit_actions,state_hashes
from .substrate import Config

NAMES=('S','C120','L','H')
GAINS=(1.,.6)
REPLICATES=(8,9,10,11,12)


def save_json(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def run_trial(n,rep,output):
    from ._brian import BrianEngine
    folder=Path(output)/f'network_{n}_replicate_{rep}';folder.mkdir(exist_ok=False)
    began=time.perf_counter_ns();engine=None
    try:
        engine=BrianEngine(Config(network_id=n,replicate_id=rep,trial_id=f'cal-n{n}-r{rep}',retain_spikes=True))
        rows=prefix_schedule();start=time.perf_counter_ns()
        prefix=engine.run_commands(schedule(engine,rows[:2350]))
        calibration=fit(tuple(x.observation for x in prefix),tuple(x.receipt for x in prefix))
        prefix+=engine.run_commands(schedule(engine,rows[2350:]))
        prefix_ns=time.perf_counter_ns()-start
        engine.save('confirmation');checkpoint=state_hashes(engine)
        prefix_counts=np.asarray(engine.monitor.count).copy()
        counts=np.empty((2,4,300,20),dtype=np.int32);filtered=np.empty((2,4,300,4))
        neurons=np.empty((2,4,1000),dtype=np.int32);delivered=np.empty((2,4,300,4))
        q=(0.,120.,*(calibration.lookup_pA or (0.,0.)));ledger=[];noise=None
        for gi,gain in enumerate(GAINS):
            for ai,name in enumerate(NAMES):
                engine.restore('confirmation')
                assert engine.time_us==51_000_000 and state_hashes(engine)==checkpoint and not np.any(engine.previous)
                engine.group.gain=gain
                desired=np.zeros((300,4));desired[:,::2]=q[ai];actions=ramp(desired)
                start=time.perf_counter_ns();result=engine.run_commands(schedule(engine,actions));wall=time.perf_counter_ns()-start
                counts[gi,ai]=[x.observation.counts for x in result]
                filtered[gi,ai]=[x.observation.filtered_sector_rate_hz for x in result]
                delivered[gi,ai]=[x.receipt.delivered_current_pA for x in result]
                np.testing.assert_array_equal(delivered[gi,ai],actions)
                for k,x in enumerate(result):
                    o=x.observation;r=x.receipt
                    assert (o.start_us,o.stop_us,o.available_us)==(51_000_000+k*20000,51_020_000+k*20000,51_020_000+k*20000)
                    assert all(o.valid) and o.coverage_us==(20000,)*20
                    assert r.requested_current_pA==r.delivered_current_pA
                    assert (r.requested_start_us,r.delivered_start_us,r.delivered_stop_us)==(o.start_us,o.start_us,o.stop_us)
                neurons[gi,ai]=np.asarray(engine.monitor.count)-prefix_counts
                for j,ids in enumerate(engine.parameters['recording']):assert counts[gi,ai,:,j].sum()==neurons[gi,ai,ids].sum()
                current_noise=dict(engine.noise_hashes)
                if noise is None:noise=current_noise
                else:assert current_noise==noise
                audit=audit_actions(actions);assert audit['constraint_violations']==0
                entry=dict(gain=gain,name=name,lookup_valid=calibration.valid if ai>=2 else True,
                    safe_fallback=ai>=2 and not calibration.valid,desired_q_pA=q[ai],
                    start_us=51_000_000,stop_us=57_000_000,simulation_call_ns=wall,
                    neural_ns=sum(x.neural_wall_ns for x in result),observation_ns=sum(x.observation_wall_ns for x in result),
                    effective_exposure_pA_s=gain*audit['total_exposure_pA_s'],
                    squared_current_pA2_s=float((actions**2).sum()*.02),**audit)
                ledger.append(entry)
                with (folder/'conditions.jsonl').open('a') as file:file.write(json.dumps(entry,allow_nan=False)+'\n')
        for array in (counts,filtered,neurons):np.testing.assert_array_equal(array[0,0],array[1,0])
        np.savez_compressed(folder/'numerical.npz',observed_counts=counts,filtered_sector_rates_hz=filtered,
            neuron_counts=neurons,delivered_current_pA=delivered,
            prefix_counts=np.array([x.observation.counts for x in prefix],dtype=np.int32),
            prefix_filtered_hz=np.array([x.observation.filtered_sector_rate_hz for x in prefix]),
            prefix_delivered_pA=np.array([x.receipt.delivered_current_pA for x in prefix]),
            stimulation=engine.parameters['stimulation'],recording=engine.parameters['recording'])
        report=dict(status='complete',network_id=n,replicate_id=rep,calibration=asdict(calibration),
            checkpoint_hashes=checkpoint,engine=engine.provenance(),receipt_ledger=ledger,
            prefix_wall_ns=prefix_ns,peak_rss_bytes=peak_rss_bytes(),total_wall_ns=time.perf_counter_ns()-began)
        save_json(folder/'trial.json',report)
        return dict(network_id=n,replicate_id=rep,status='complete',wall_ns=report['total_wall_ns'])
    except Exception as error:
        failure=dict(network_id=n,replicate_id=rep,status='failed',error=f'{type(error).__name__}: {error}')
        save_json(folder/'failure.json',failure);return failure
    finally:
        if engine is not None:engine.close()
        del engine;gc.collect()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
    os.environ.setdefault('MPLCONFIGDIR','/tmp/neuromancer-m0023-mpl')
    prereg=Path(__file__).resolve().parents[2]/'reports/evidence/m002_3/PREREGISTRATION.md'
    record=provenance();record.update(preregistration_sha256=hashlib.sha256(prereg.read_bytes()).hexdigest(),
        design=dict(network_ids=list(range(10)),replicate_ids=REPLICATES,gains=GAINS,names=NAMES,
        prefix_us=51_000_000,duration_us=6_000_000,simulated_seconds=4950,workers=3,wall_limit_s=4500))
    save_json(args.output/'provenance.json',record)
    began=time.perf_counter_ns();results=[]
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        futures=[pool.submit(run_trial,n,r,str(args.output)) for n in range(10) for r in REPLICATES]
        try:
            for future in as_completed(futures,timeout=4500):
                result=future.result();results.append(result);print(f'{len(results)}/50 {result}',flush=True)
                save_json(args.output/'progress.json',results)
        except TimeoutError:
            for process in pool._processes.values():process.terminate()
            raise SystemExit('75min scientific budget exceeded; partial evidence retained')
    hashes={str(p.relative_to(args.output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.output.rglob('*')) if p.is_file()}
    summary=dict(status='complete' if all(x['status']=='complete' for x in results) else 'partial',
        trials=sorted(results,key=lambda x:(x['network_id'],x['replicate_id'])),wall_ns=time.perf_counter_ns()-began,artifact_sha256=hashes)
    save_json(args.output/'summary.json',summary)
    if summary['status']!='complete':raise SystemExit('Incomplete fixed cohort; see retained failures')


if __name__=='__main__':main()
