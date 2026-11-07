"""M004 uninterrupted acquisition; counterfactual branches are evaluator-only."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
import gc
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import time
import numpy as np
from .calibration import ramp
from .calibration_diagnostic import save_json
from .diagnostic import provenance, schedule, peak_rss_bytes
from .identification_experiment import excitation
from .state_experiment import arrays
from .reachability import state_hashes
from .substrate import Config

ORIGINS = (54, 64, 74)


def actions(config, weak=False):
    desired = np.vstack([np.zeros((750, 4)), excitation(config, 2, 40), excitation(config, 1, 41), excitation(config, 5, 42)])
    if weak: desired[:] = 0
    return desired, ramp(desired)


def branch_audit(u, previous):
    slew = np.diff(np.vstack([previous, u]), axis=0)
    violations = int(((u < 0)|(u > 120)).sum()+(u.sum(axis=1) > 240).sum()+(abs(slew) > 30).sum())
    return dict(violations=violations, exposure_pA_s=float(u.sum()*.02), nominal_charge_pC=float(u.sum()*.02*50),
                maximum_total_pA=float(u.sum(axis=1).max()), maximum_slew_pA=float(abs(slew).max()))


def run_trial(n, rep, condition, output):
    from ._brian import BrianEngine
    folder = Path(output)/f'n{n}_r{rep}_{condition}'; folder.mkdir(exist_ok=False)
    engine = None; began = time.perf_counter_ns()
    try:
        config = Config(network_id=n, replicate_id=rep, trial_id=f'm004-n{n}-r{rep}-{condition}', efficacy=0. if condition == 'NULL' else 1.)
        engine = BrianEngine(config); desired, planned = actions(config, condition == 'WEAK')
        np.savez_compressed(folder/'plans.npz', desired=desired, planned=planned)
        checkpoints = {}; results = []; gain = np.ones(3950)*(0. if condition == 'NULL' else 1.)
        if condition in ('LOSS', 'WEAK'): gain[2950:] = .6
        elif condition == 'UP': gain[2950:] = 1.4
        for stop in (54, 59, 64, 74, 79):
            start = engine.time_us//20000; engine.group.gain = gain[start]
            results.extend(engine.run_commands(schedule(engine, planned[start:stop*50])))
            if stop in ORIGINS:
                engine.save(str(stop)); checkpoints[str(stop)] = state_hashes(engine)
        assert engine.time_us == 79_000_000
        primary = arrays(results); np.testing.assert_array_equal(primary['delivered'], planned)
        np.savez_compressed(folder/'public.npz', **primary)
        np.savez_compressed(folder/'evaluator.npz', gain=gain, recording=engine.parameters['recording'], stimulation=engine.parameters['stimulation'])
        primary_provenance = engine.provenance(); ledger = []
        for origin in ORIGINS:
            k = origin*50; engine.restore(str(origin)); assert state_hashes(engine) == checkpoints[str(origin)]
            previous = engine.previous.copy(); sham = np.maximum(previous[None, :]-30*np.arange(1, 51)[:, None], 0.)
            rows = np.stack([planned[k:k+50], sham]); np.savez_compressed(folder/f'probe{origin}_plans.npz', planned=rows, previous=previous)
            noise = None; zero = None
            for j, name in enumerate(('active', 'sham')):
                engine.restore(str(origin)); assert state_hashes(engine) == checkpoints[str(origin)]
                engine.group.gain = gain[k]; before = np.array(engine.monitor.count).copy(); started = time.perf_counter_ns()
                result = engine.run_commands(schedule(engine, rows[j])); elapsed = time.perf_counter_ns()-started
                d = arrays(result); neurons = np.asarray(engine.monitor.count).copy()-before
                if j == 0:
                    for field in ('counts', 'rates', 'sector', 'delivered'): np.testing.assert_array_equal(d[field], primary[field][k:k+50])
                    zero = d
                elif condition == 'NULL':
                    for field in ('counts', 'rates', 'sector', 'event_time_us', 'event_channel'): np.testing.assert_array_equal(d[field], zero[field])
                if noise is None: noise = dict(engine.noise_hashes)
                else: assert engine.noise_hashes == noise
                np.savez_compressed(folder/f'probe{origin}_{name}.npz', **d, neurons=neurons)
                entry = dict(origin_s=origin, branch=name, wall_ns=elapsed, **branch_audit(rows[j], previous))
                assert entry['violations'] == 0; ledger.append(entry)
        report = dict(status='complete', network_id=n, replicate_id=rep, condition=condition, engine=primary_provenance,
                      checkpoints=checkpoints, probes=ledger, primary_audit=branch_audit(planned, np.zeros(4)),
                      wall_ns=time.perf_counter_ns()-began, peak_rss_bytes=peak_rss_bytes())
        save_json(folder/'trial.json', report)
        return {k: report[k] for k in ('status', 'network_id', 'replicate_id', 'condition', 'wall_ns')}
    except Exception as e:
        report = dict(status='failed', network_id=n, replicate_id=rep, condition=condition, error=f'{type(e).__name__}: {e}')
        save_json(folder/'failure.json', report); return report
    finally:
        if engine is not None: engine.close()
        del engine; gc.collect()


def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage', choices=('D', 'V'), required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--selection', type=Path); args = p.parse_args()
    if args.stage == 'V':
        if args.selection is None: raise SystemExit('Sealed development selection required')
        selection = json.loads(args.selection.read_text()); assert selection['frozen']
    args.output.mkdir(parents=True, exist_ok=False)
    if args.stage == 'D':
        jobs = [(n, r, c) for n in range(10) for r in (32, 33) for c in ('STATIC', 'LOSS')]+[(n, 32, 'UP') for n in range(10)]+[(n, 36, 'NULL') for n in range(3)]+[(n, 35, 'WEAK') for n in range(3)]
        limit = 3600
    else: jobs = [(n, r, c) for n in range(10, 15) for r in (32, 33) for c in ('STATIC', 'LOSS')]; limit = 1500
    record = provenance(); record.update(stage=args.stage, jobs=jobs, wall_limit_s=limit, simulated_seconds=85*len(jobs),
        protocol_sha256=hashlib.sha256(Path('docs/research/008_M004_ONLINE_IDENTIFICATION_PROTOCOL.md').read_bytes()).hexdigest())
    if args.selection: record['selection_sha256'] = hashlib.sha256(args.selection.read_bytes()).hexdigest()
    save_json(args.output/'provenance.json', record); began = time.perf_counter_ns(); results = []
    with ProcessPoolExecutor(max_workers=3, mp_context=mp.get_context('spawn')) as pool:
        futures = [pool.submit(run_trial, n, r, c, str(args.output)) for n, r, c in jobs]
        try:
            for future in as_completed(futures, timeout=limit):
                result = future.result(); results.append(result); print(f'{len(results)}/{len(jobs)} {result}', flush=True)
                save_json(args.output/'progress.json', results)
        except TimeoutError:
            for proc in pool._processes.values(): proc.terminate()
            raise SystemExit('Acquisition cap; partial evidence retained')
    save_json(args.output/'summary.json', dict(status='complete' if all(r['status']=='complete' for r in results) else 'partial', trials=results, wall_ns=time.perf_counter_ns()-began))
    if any(r['status'] != 'complete' for r in results): raise SystemExit('Incomplete acquisition')


if __name__ == '__main__': main()
