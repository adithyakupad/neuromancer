"""M005A bounded sample-and-hold feedback acquisition; evaluator owns gain."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from dataclasses import asdict
import gc
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import time
import numpy as np
from .calibration import prefix_schedule
from .calibration_diagnostic import save_json
from .control import GAINS, Policy, calibrate, project
from .diagnostic import schedule, provenance, peak_rss_bytes
from .online_experiment import branch_audit
from .reachability import state_hashes
from .state_experiment import arrays
from .substrate import Config


def run_trial(n, rep, names, output):
    from ._brian import BrianEngine
    folder = Path(output)/f'n{n}_r{rep}'; folder.mkdir(exist_ok=False)
    engine = None; began = time.perf_counter_ns()
    try:
        engine = BrianEngine(Config(network_id=n, replicate_id=rep, trial_id=f'm005a-n{n}-r{rep}'))
        prefix = engine.run_commands(schedule(engine, prefix_schedule()))
        calibration = calibrate([r.observation for r in prefix[:2350]], [r.receipt for r in prefix[:2350]])
        save_json(folder/'calibration.json', asdict(calibration))
        np.savez_compressed(folder/'prefix.npz', **arrays(prefix))
        engine.save('control'); initial = state_hashes(engine); branches = []
        for condition in ('STATIC', 'LOSS'):
            for name in names:
                engine.restore('control'); assert state_hashes(engine) == initial
                policy = Policy(calibration, name); results = []; intentions = []; decisions = []; timing = []
                start_ns = time.perf_counter_ns(); initial_noise = dict(engine.noise_hashes)
                for second in range(32):
                    # Evaluator only. No gain/change-time object enters Policy.
                    engine.group.gain = .6 if condition == 'LOSS' and second >= 16 else 1.
                    t0 = time.perf_counter_ns(); desired = policy.desired(); decisions.append(policy.record())
                    rows = []; previous = engine.previous.copy()
                    for _ in range(50):
                        delivered, status = project(desired, previous)
                        assert 'invalid' not in status
                        rows.append(delivered); previous = delivered
                    intentions.extend([desired.copy() for _ in range(50)])
                    planning_ns = time.perf_counter_ns()-t0
                    # Equivalent to50 feedback_step calls with no policy update
                    # before50 complete bins. Valid-only batching: unexpected gaps
                    # abort this scientific trial; the general tick API handles gaps.
                    block = engine.run_commands(schedule(engine, rows))
                    t0 = time.perf_counter_ns()
                    for r in block:
                        policy.accept(r.observation, r.observation.available_us)
                        if policy.safe and calibration.valid:
                            raise RuntimeError('Base-case fallback or invalid calibration')
                    timing.append((planning_ns, time.perf_counter_ns()-t0,
                                   sum(r.neural_wall_ns for r in block), sum(r.observation_wall_ns for r in block)))
                    results.extend(block)
                data = arrays(results); audit = branch_audit(data['delivered'], np.zeros(4)); assert audit['violations'] == 0
                np.savez_compressed(folder/f'{condition}_{name}.npz', **data, intent=np.array(intentions),
                                    decisions=np.array(decisions), terminal=np.array(policy.record()), timings_ns=np.array(timing))
                branches.append(dict(condition=condition, controller=name, wall_ns=time.perf_counter_ns()-start_ns,
                                     audit=audit, initial_noise=initial_noise, noise=engine.provenance()['noise_hashes']))
        save_json(folder/'trial.json', dict(status='complete', network_id=n, replicate_id=rep,
                  calibration=asdict(calibration), engine=engine.provenance(), checkpoint=initial,
                  branches=branches, prefix_audit=branch_audit(prefix_schedule(), np.zeros(4)),
                  wall_ns=time.perf_counter_ns()-began, peak_rss_bytes=peak_rss_bytes()))
        return dict(status='complete', network_id=n, replicate_id=rep, wall_ns=time.perf_counter_ns()-began)
    except Exception as e:
        if 'results' in locals() and results:
            np.savez_compressed(folder/'partial.npz', **arrays(results))
        record = dict(status='failed', network_id=n, replicate_id=rep, error=f'{type(e).__name__}: {e}')
        save_json(folder/'failure.json', record); return record
    finally:
        if engine is not None: engine.close()
        del engine; gc.collect()


def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage', choices=('TUNE', 'CONFIRM'), required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--selection', type=Path); args = p.parse_args()
    names = ('ZERO', 'FIXED', 'MAX', *GAINS)
    reps = (40,); limit = 3600
    if args.stage == 'CONFIRM':
        if args.selection is None: raise SystemExit('Committed selection required')
        selection = json.loads(args.selection.read_text()); assert selection['frozen']
        names = ('ZERO', 'FIXED', 'MAX', selection['controller']); reps = (41, 42); limit = 5400
    args.output.mkdir(parents=True, exist_ok=False)
    record = provenance(); record.update(stage=args.stage, names=names, replicates=reps, networks=list(range(10)),
        wall_limit_s=limit, simulated_seconds=(51+32*2*len(names))*10*len(reps),
        protocol_sha256=hashlib.sha256(Path('docs/research/009_M005A_CONTROL_PROTOCOL.md').read_bytes()).hexdigest())
    if args.selection: record['selection_sha256'] = hashlib.sha256(args.selection.read_bytes()).hexdigest()
    save_json(args.output/'provenance.json', record); began = time.perf_counter_ns(); results = []
    with ProcessPoolExecutor(max_workers=3, mp_context=mp.get_context('spawn')) as pool:
        futures = [pool.submit(run_trial, n, rep, names, str(args.output)) for n in range(10) for rep in reps]
        try:
            for future in as_completed(futures, timeout=limit):
                r = future.result(); results.append(r); print(f'{len(results)}/{len(futures)} {r}', flush=True)
                save_json(args.output/'progress.json', results)
                # Calibration failures are scientific outcomes: keep all trials.
        except TimeoutError:
            for proc in pool._processes.values(): proc.terminate()
            raise SystemExit('Resource cap; partial evidence retained')
    save_json(args.output/'summary.json', dict(status='complete' if all(r['status']=='complete' for r in results) else 'partial',
                                             trials=results, wall_ns=time.perf_counter_ns()-began))
    if any(r['status'] != 'complete' for r in results): raise SystemExit('Incomplete acquisition')


if __name__ == '__main__': main()
