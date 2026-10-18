"""Bounded evaluator diagnostics; no controllers, fitting, or held-out networks."""
import argparse
from dataclasses import asdict
import gc
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import numpy as np
from .substrate import Command, Config, Trial


def schedule(engine, values):
    return [Command(engine.config.trial_id, f'c{engine.time_us+i*20000}',
                    engine.time_us+i*20000, tuple(map(float, row)))
            for i, row in enumerate(values)]


def run_hold(engine, seconds, amplitude, *, chunked=False):
    count = round(seconds/.02)
    rows = np.full((count,4),float(amplitude))
    for i in range(count):
        previous = engine.previous if i==0 else rows[i-1]
        rows[i] = np.clip(rows[i],previous-30,previous+30)
    started = time.perf_counter_ns()
    results = engine.run_commands(schedule(engine,rows),chunked=chunked)
    wall_ns = time.perf_counter_ns()-started
    return results, wall_ns


def rates(results):
    return np.array([r.observation.sector_rate_hz for r in results])


def peak_rss_bytes():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform=='darwin' else rss*1024)


def _performance_worker(connection, retain, chunked):
    try:
        from ._brian import BrianEngine
        engine=BrianEngine(Config(retain_spikes=retain))
        results,wall=run_hold(engine,5,0,chunked=chunked)
        connection.send(dict(retain_spikes=retain,chunked=chunked,
            initialization_ns=engine.initialization_ns,simulated_seconds=5,
            wall_ns=wall,neural_ns=sum(r.neural_wall_ns for r in results),
            observation_ns=sum(r.observation_wall_ns for r in results),
            realtime_factor=5/(wall/1e9),peak_rss_bytes=peak_rss_bytes(),
            retained_spike_events=len(engine.monitor.i),
            retained_event_array_bytes=np.asarray(engine.monitor.i).nbytes+np.asarray(engine.monitor.t).nbytes,
            population_spikes=int(sum(engine.monitor.count)),
            observed_spikes=int(sum(sum(r.observation.counts) for r in results)),
            provenance=engine.provenance()))
    except Exception as error:
        connection.send(dict(error=f'{type(error).__name__}: {error}'))
    finally:
        connection.close()


def performance(output):
    context=mp.get_context('spawn')
    cases=[]
    for retain in (False,True):
        for chunked in (False,True):
            parent,child=context.Pipe()
            process=context.Process(target=_performance_worker,args=(child,retain,chunked))
            process.start();child.close()
            if not parent.poll(180):
                process.terminate();process.join()
                raise RuntimeError('Performance probe exceeded 180 second bound')
            result=parent.recv();parent.close();process.join(timeout=5)
            if process.is_alive():
                process.terminate();process.join()
                raise RuntimeError('Performance process failed to stop')
            if process.exitcode!=0 or 'error' in result:raise RuntimeError(str(result))
            cases.append(result)
            print('performance',retain,chunked,result['wall_ns']/1e9,flush=True)
    numerical=[(r['population_spikes'],r['observed_spikes']) for r in cases]
    if len(set(numerical))!=1:raise RuntimeError('Retention/chunking changed spike counts')
    (output/'performance.json').write_text(json.dumps(dict(cases=cases,
        repetitions_per_case=1,limitations='Fresh process each; one timing sample, includes noise generation; peak RSS is process high-water, not incremental retention memory.'),indent=2)+'\n')
    return cases


def authority(output):
    from ._brian import BrianEngine
    records=[]
    for network_id in range(10):
        engine=BrianEngine(Config(network_id=network_id,trial_id=f'train-{network_id}'))
        began=time.perf_counter_ns()
        run_hold(engine,5,0)
        baseline,_=run_hold(engine,10,0)
        base_rates=rates(baseline)[100:]
        engine.save('baseline')
        sham,_=run_hold(engine,5,0)
        engine.restore('baseline')
        stim,_=run_hold(engine,5,60)
        engine.restore('baseline')
        engine.group.gain=.6
        reduced,_=run_hold(engine,5,60)
        sham_rate=rates(sham).mean()
        response=rates(stim).mean()-sham_rate
        response_06=rates(reduced).mean()-sham_rate
        row=dict(network_id=network_id,replicate_id=0,
            baseline_recorded_E_hz=float(base_rates.mean()),
            maximum_sector_8s_mean_hz=float(base_rates.mean(axis=0).max()),
            maximum_sector_20ms_bin_hz=float(base_rates.max()),
            sham_hz=float(sham_rate),stimulus_g1_hz=float(rates(stim).mean()),
            stimulus_g06_hz=float(rates(reduced).mean()),
            contrast_g1_hz=float(response),contrast_g06_hz=float(response_06),
            activity_gate=bool(1<=base_rates.mean()<=30 and base_rates.mean(axis=0).max()<100),
            authority_4hz_at_g06=bool(response_06>=4),
            finite_state=True,wall_ns=time.perf_counter_ns()-began,
            provenance=engine.provenance())
        records.append(row)
        np.savez_compressed(output/f'authority_network_{network_id}.npz',
            baseline_sector_hz=rates(baseline),sham_sector_hz=rates(sham),
            stimulus_g1_sector_hz=rates(stim),stimulus_g06_sector_hz=rates(reduced),
            delivered_current_pA=np.array([r.receipt.delivered_current_pA for r in reduced]),
            filter_baseline_hz=np.array(baseline[-1].observation.filtered_sector_rate_hz),
            **engine.parameters)
        (output/f'network_{network_id}.json').write_text(json.dumps(row,indent=2)+'\n')
        print('authority',network_id,row['baseline_recorded_E_hz'],response,response_06,flush=True)
        engine.close();del engine;gc.collect()
    count=sum(r['authority_4hz_at_g06'] for r in records)
    summary=dict(networks=records,authority_pass_count=count,
        gate='PASS' if count>=8 else 'FAIL',
        activity_pass_count=sum(r['activity_gate'] for r in records),
        inference='Descriptive paired same-noise 5 s holds, one noise replicate/network; no independent-replicate confidence intervals.',
        positive_randomized_input_ci_gate='NOT RUN: fixed-hold authority is a prerequisite; no CI over correlated bins is substituted.')
    (output/'authority.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def convergence(output):
    from ._brian import BrianEngine
    rows=[]
    for network_id in range(3):
        cases=[]
        for dt in (100,50):
            engine=BrianEngine(Config(network_id=network_id,dt_us=dt))
            run_hold(engine,5,0)
            engine.save('burn')
            sham,_=run_hold(engine,5,0)
            engine.restore('burn')
            stim,_=run_hold(engine,5,60)
            cases.append(dict(dt_us=dt,sham_hz=float(rates(sham).mean()),
                response_hz=float(rates(stim).mean()-rates(sham).mean()),provenance=engine.provenance()))
            engine.close();del engine;gc.collect()
        difference=lambda key:abs(cases[0][key]-cases[1][key])
        # Protocol tolerance: 5% with a 0.5 Hz absolute floor.
        rate_bound=max(.5,.05*abs(cases[1]['sham_hz']))
        response_bound=max(.5,.05*abs(cases[1]['response_hz']))
        row=dict(network_id=network_id,cases=cases,
            rate_difference_hz=difference('sham_hz'),rate_tolerance_hz=rate_bound,
            response_difference_hz=difference('response_hz'),response_tolerance_hz=response_bound,
            passed=bool(difference('sham_hz')<=rate_bound and difference('response_hz')<=response_bound))
        rows.append(row);print('convergence',network_id,row['passed'],flush=True)
    result=dict(networks=rows,gate='PASS' if all(r['passed'] for r in rows) else 'FAIL',
        limitation='Paired nested OU innovations; one finite-duration realization per network, no equality of spikes across dt asserted. Held-current response rather than short-pulse convergence.')
    (output/'convergence.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def smoke(output):
    observations=[]
    with Trial(Config(trial_id='smoke')) as trial:
        metadata=trial.metadata
        for k in range(10):
            command=Command('smoke',str(k),k*20000,(30.,)*4 if k<5 else (0.,)*4)
            observations.append(asdict(trial.advance(command,(k+1)*20000)))
    with (output/'steps.jsonl').open('w') as file:
        for row in observations:
            # The baseline-dependent filter is explicitly unavailable pre-baseline.
            row['observation']['filtered_sector_rate_hz']=[None]*4
            file.write(json.dumps(row,allow_nan=False)+'\n')
    (output/'smoke.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return observations


def plot_results(output):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.hashsalt':'neuromancer-m002'})
    if (output/'authority.json').exists():
        results=json.loads((output/'authority.json').read_text())['networks']
        fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
        ids=[r['network_id'] for r in results]
        axes[0].plot(ids,[r['baseline_recorded_E_hz'] for r in results],'o-')
        axes[0].set(xlabel='Training network',ylabel='Observed E rate (Hz)',title='Last 8 s of baseline')
        for key,label in [('contrast_g1_hz','Efficacy 1'),('contrast_g06_hz','Efficacy 0.6')]:
            axes[1].plot(ids,[r[key] for r in results],'o-',label=label)
        axes[1].axhline(4,color='black',linestyle='--',label='4 Hz authority gate')
        axes[1].set(xlabel='Training network',ylabel='Paired stimulation − sham (Hz)',title='5 s constrained holds')
        axes[1].legend(fontsize=8)
        fig.savefig(output/'authority.svg',metadata={'Date':None});plt.close(fig)
    elif (output/'steps.jsonl').exists():
        rows=[json.loads(line)['observation'] for line in (output/'steps.jsonl').read_text().splitlines()]
        fig,axes=plt.subplots(2,1,figsize=(7,4),layout='constrained')
        for row in rows:
            axes[0].scatter(np.array(row['event_time_us'])/1000,row['channel_id'],s=3,color='black')
        axes[0].set(xlabel='Simulation time (ms)',ylabel='Recording channel',title='Simulation-only observed spikes')
        axes[1].plot([r['stop_us']/1000 for r in rows],[np.mean(r['sector_rate_hz']) for r in rows])
        axes[1].set(xlabel='Completed bin edge (ms)',ylabel='Observed E rate (Hz)')
        fig.savefig(output/'smoke.svg',metadata={'Date':None});plt.close(fig)


def provenance():
    root=Path(__file__).resolve().parents[2]
    def git(*args):
        return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((root/'src/neuromancer').glob('*.py'))}
    protocol=root/'docs/research/002_V0_PROTOCOL.md'
    return dict(schema_version=1,experiment_kind='simulation',head=git('rev-parse','HEAD'),
        branch=git('branch','--show-current'),working_tree=git('status','--porcelain=v1'),
        source_hashes=sources,protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),
        python=sys.version,platform=platform.platform(),machine=platform.machine(),
        package_versions={p:importlib.metadata.version(p) for p in ['neuromancer','brian2','numpy','sympy','cython']},
        cli=sys.argv,clock='integer us; 100 us neural grid and 20000 us control bins',
        evaluated_split='training only; IDs 0-9, or 0-2 for convergence')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['smoke','authority','performance','convergence'],default='smoke')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'provenance.json').write_text(json.dumps(provenance(),indent=2)+'\n')
    try:
        {'smoke':smoke,'authority':authority,'performance':performance,'convergence':convergence}[args.mode](args.output)
        plot_results(args.output)
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(args.output.iterdir()) if p.is_file()}
        terminal=dict(status='complete',mode=args.mode,artifact_sha256=hashes)
    except Exception as error:
        (args.output/'failure.json').write_text(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'),indent=2)+'\n')
        raise
    temporary=args.output/'summary.tmp'
    temporary.write_text(json.dumps(terminal,indent=2)+'\n')
    temporary.replace(args.output/'summary.json')


if __name__=='__main__':
    main()
