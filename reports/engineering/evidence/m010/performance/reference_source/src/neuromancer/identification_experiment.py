"""M003 fixed neural acquisition; prediction/selection never reads private state."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed,TimeoutError
import gc
import hashlib
import itertools
import json
import multiprocessing as mp
import os
from pathlib import Path
import time
import numpy as np
from .calibration import ramp
from .calibration_diagnostic import save_json
from .diagnostic import provenance,schedule,peak_rss_bytes
from .reachability import state_hashes
from .substrate import Config

NAMES=('S','P01','P12','P23','P03','R')


def bank():
    rows=[np.zeros(4)]
    for value in (30,90):
        for j in range(4):
            row=np.zeros(4);row[j]=value;rows.append(row)
    for pair in itertools.combinations(range(4),2):
        row=np.zeros(4);row[list(pair)]=120;rows.append(row)
    rows.append(np.full(4,60.));return np.array(rows)


def excitation(config,cycles,block):
    from ._brian import stream
    rng=stream(config,5,block=block);vectors=bank()
    order=np.concatenate([rng.permutation(16) for _ in range(cycles)])
    desired=np.zeros((len(order)*25,4))
    for i,a in enumerate(order):desired[i*25+5:(i+1)*25]=vectors[a]
    return desired


def schedules(config):
    prefix=np.vstack([np.zeros((750,4)),excitation(config,4,0),excitation(config,1,1),excitation(config,1,2),np.zeros((200,4))])
    desired=np.zeros((6,100,4))
    for i,pair in enumerate(((0,1),(1,2),(2,3),(0,3)),1):desired[i,:25,list(pair)]=120
    desired[5]=excitation(config,1,3)[:100]
    planned=np.array([ramp(row) for row in desired])
    actual_prefix=ramp(prefix)
    for rows in [actual_prefix,*planned]:assert audit(rows)['violations']==0
    return prefix,actual_prefix,desired,planned


def audit(rows):
    rows=np.asarray(rows)
    if rows.ndim!=2 or rows.shape[1]!=4 or not np.isfinite(rows).all():raise ValueError('Invalid current schedule')
    slew=np.diff(np.vstack([np.zeros(4),rows]),axis=0)
    return dict(violations=int(((rows<0)|(rows>120)).sum()+(rows.sum(axis=1)>240).sum()+(np.abs(slew)>30).sum()),
        exposure_pA_s=float(rows.sum()*.02),model_charge_pC=float(rows.sum()*.02*50),
        maximum_total_pA=float(rows.sum(axis=1).max()),maximum_slew_pA=float(np.abs(slew).max()))


def run_trial(n,rep,gain,output,stationary):
    from ._brian import BrianEngine
    folder=Path(output)/f'n{n}_r{rep}';folder.mkdir(exist_ok=False);engine=None;began=time.perf_counter_ns()
    try:
        config=Config(network_id=n,replicate_id=rep,trial_id=f'id-n{n}-r{rep}',efficacy=0. if gain==0 else 1.)
        engine=BrianEngine(config);desired_prefix,prefix,desired,planned=schedules(config)
        results=engine.run_commands(schedule(engine,prefix))
        def extract(result,start):
            for k,x in enumerate(result):
                o=x.observation;r=x.receipt;t=start+k*20000
                assert (o.start_us,o.stop_us,o.available_us)==(t,t+20000,t+20000)
                assert o.valid==(True,)*20 and o.coverage_us==(20000,)*20
                assert (r.requested_start_us,r.delivered_start_us,r.delivered_stop_us)==(t,t,t+20000)
                assert r.requested_current_pA==r.delivered_current_pA
            return dict(counts=np.array([x.observation.counts for x in result],dtype=np.int32),
                rates=np.array([x.observation.filtered_sector_rate_hz for x in result]),
                delivered=np.array([x.receipt.delivered_current_pA for x in result]))
        observed=extract(results,0);np.testing.assert_array_equal(observed['delivered'],prefix)
        if stationary:
            with np.load(Path(stationary)/folder.name/'prefix.npz',allow_pickle=False) as old:
                for key in observed:np.testing.assert_array_equal(observed[key],old[key])
        np.savez_compressed(folder/'prefix.npz',**observed,desired=desired_prefix,planned=prefix)
        np.savez_compressed(folder/'plans.npz',desired=desired,planned=planned)
        engine.save('origin');checkpoint=state_hashes(engine);prefix_spikes=np.asarray(engine.monitor.count).copy()
        counts=np.empty((6,100,20),dtype=np.int32);rates=np.empty((6,100,4));delivered=np.empty((6,100,4));neurons=np.empty((6,1000),dtype=np.int32)
        ledger=[];noise=None
        for i,name in enumerate(NAMES):
            engine.restore('origin');assert state_hashes(engine)==checkpoint and engine.time_us==67_000_000 and not engine.previous.any()
            engine.group.gain=gain;start=time.perf_counter_ns();result=engine.run_commands(schedule(engine,planned[i]));wall=time.perf_counter_ns()-start
            actual=extract(result,67_000_000);counts[i]=actual['counts'];rates[i]=actual['rates'];delivered[i]=actual['delivered']
            np.testing.assert_array_equal(delivered[i],planned[i]);neurons[i]=np.asarray(engine.monitor.count)-prefix_spikes
            for c,ids in enumerate(engine.parameters['recording']):assert counts[i,:,c].sum()==neurons[i,ids].sum()
            if noise is None:noise=dict(engine.noise_hashes)
            else:assert engine.noise_hashes==noise
            entry=dict(name=name,gain=gain,**audit(delivered[i]),wall_ns=wall,
                neural_ns=sum(x.neural_wall_ns for x in result),observation_ns=sum(x.observation_wall_ns for x in result))
            assert entry['violations']==0;ledger.append(entry)
            with (folder/'conditions.jsonl').open('a') as file:file.write(json.dumps(entry)+'\n')
        if gain==0:
            for array in (counts,rates,neurons):
                for i in range(6):np.testing.assert_array_equal(array[i],array[0])
        np.savez_compressed(folder/'confirmation.npz',counts=counts,rates=rates,delivered=delivered,neurons=neurons,
            recording=engine.parameters['recording'],stimulation=engine.parameters['stimulation'])
        report=dict(status='complete',network_id=n,replicate_id=rep,gain=gain,engine=engine.provenance(),
            checkpoint_hashes=checkpoint,receipts=ledger,prefix_audit=audit(prefix),peak_rss_bytes=peak_rss_bytes(),wall_ns=time.perf_counter_ns()-began)
        save_json(folder/'trial.json',report)
        return dict(network_id=n,replicate_id=rep,gain=gain,status='complete',wall_ns=report['wall_ns'])
    except Exception as error:
        failure=dict(status='failed',network_id=n,replicate_id=rep,error=f'{type(error).__name__}: {error}')
        save_json(folder/'failure.json',failure);return failure
    finally:
        if engine is not None:engine.close()
        del engine;gc.collect()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=('D','V','G'),required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--qualification',type=Path);parser.add_argument('--stationary',type=Path)
    args=parser.parse_args()
    if args.stage!='D':
        if not args.qualification or json.loads(args.qualification.read_text())['scientific_gate']!='PASS':raise SystemExit('Development qualification required')
    if args.stage=='G' and not args.stationary:raise SystemExit('Stationary replay required')
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ.setdefault('MPLCONFIGDIR','/tmp/neuromancer-m003-mpl')
    if args.stage=='D':jobs=[(n,r,1.) for n in range(10) for r in (18,19,20)]+[(n,21,0.) for n in range(3)];limit=2700
    elif args.stage=='V':jobs=[(n,r,1.) for n in range(10,15) for r in (18,19,20)];limit=1500
    else:jobs=[(n,18,.6) for n in range(10)];limit=1200
    protocol=Path(__file__).resolve().parents[2]/'docs/research/005_M003_IDENTIFICATION_PROTOCOL.md'
    record=provenance();record.update(stage=args.stage,evaluated_split='development0-9 and null0-2' if args.stage=='D' else 'validation10-14' if args.stage=='V' else 'development0-9 stress',
        m003_protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),jobs=jobs,wall_limit_s=limit,simulated_seconds=len(jobs)*79)
    clarification=protocol.parents[2]/'reports/evidence/m003/PREREGISTRATION_CLARIFICATION_001.md'
    record['preregistration_files_sha256']={str(p.relative_to(protocol.parents[2])):hashlib.sha256(p.read_bytes()).hexdigest() for p in (protocol,clarification)}
    if args.qualification:record['qualification_sha256']=hashlib.sha256(args.qualification.read_bytes()).hexdigest()
    save_json(args.output/'provenance.json',record);began=time.perf_counter_ns();results=[]
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        futures=[pool.submit(run_trial,n,r,g,str(args.output),str(args.stationary) if args.stationary else None) for n,r,g in jobs]
        try:
            for future in as_completed(futures,timeout=limit):
                result=future.result();results.append(result);print(f'{len(results)}/{len(jobs)} {result}',flush=True);save_json(args.output/'progress.json',results)
        except TimeoutError:
            for process in pool._processes.values():process.terminate()
            raise SystemExit('Resource ceiling reached; partial evidence retained')
    hashes={str(f.relative_to(args.output)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(args.output.rglob('*')) if f.is_file()}
    save_json(args.output/'summary.json',dict(status='complete' if all(x['status']=='complete' for x in results) else 'partial',
        trials=results,wall_ns=time.perf_counter_ns()-began,artifact_sha256=hashes))
    if any(x['status']!='complete' for x in results):raise SystemExit('Incomplete cohort; see retained failures')


if __name__=='__main__':main()
