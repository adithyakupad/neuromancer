"""M005A bounded sample-and-hold feedback acquisition; evaluator owns gain."""
import argparse
from dataclasses import asdict
import gc
import hashlib
import json
import os
import sys
from pathlib import Path
import time
import numpy as np
from .calibration import prefix_schedule
from .control import GAINS, Policy, calibrate, project
from .diagnostic import schedule, provenance, peak_rss_bytes
from .online_experiment import branch_audit
from .reachability import state_hashes
from .state_experiment import arrays
from .substrate import Config
from .supervisor import Deadline, atomic_json, supervise
from .clocks import now_ns, clock_domain

save_json = atomic_json


def _save_npz(path, **data):
    # Forced termination may leave .tmp, never a partially published archive.
    temp = path.with_name(path.name + '.tmp')
    with temp.open('wb') as stream:
        np.savez_compressed(stream, **data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def check_deadline(deadline_epoch_s, now_epoch_s=None):
    """Legacy epoch helper retained for historical fixtures; not used by acquisition."""
    if deadline_epoch_s is not None and (time.time() if now_epoch_s is None else now_epoch_s) > deadline_epoch_s:
        raise TimeoutError('Absolute acquisition wall-time cap exceeded')


def run_trial(n, rep, names, output, deadline_ns):
    from ._brian import BrianEngine
    folder = Path(output)/f'n{n}_r{rep}'; folder.mkdir(exist_ok=False)
    engine = None; began = time.perf_counter_ns()
    try:
        _check_worker(deadline_ns)
        engine = BrianEngine(Config(network_id=n, replicate_id=rep, trial_id=f'm005a-n{n}-r{rep}'))
        prefix = engine.run_commands(schedule(engine, prefix_schedule()))
        calibration = calibrate([r.observation for r in prefix[:2350]], [r.receipt for r in prefix[:2350]])
        save_json(folder/'calibration.json', asdict(calibration))
        _save_npz(folder/'prefix.npz', **arrays(prefix))
        _check_worker(deadline_ns)
        engine.save('control'); initial = state_hashes(engine); branches = []
        for condition in ('STATIC', 'LOSS'):
            for name in names:
                engine.restore('control'); assert state_hashes(engine) == initial
                policy = Policy(calibration, name); results = []; intentions = []; decisions = []; timing = []
                start_ns = time.perf_counter_ns(); initial_noise = dict(engine.noise_hashes)
                for second in range(32):
                    _check_worker(deadline_ns)
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
                _save_npz(folder/f'{condition}_{name}.npz', **data, intent=np.array(intentions),
                                    decisions=np.array(decisions), terminal=np.array(policy.record()), timings_ns=np.array(timing))
                branches.append(dict(condition=condition, controller=name, wall_ns=time.perf_counter_ns()-start_ns,
                                     audit=audit, initial_noise=initial_noise, noise=engine.provenance()['noise_hashes']))
        _check_worker(deadline_ns)
        save_json(folder/'trial.json', dict(status='complete', network_id=n, replicate_id=rep,
                  calibration=asdict(calibration), engine=engine.provenance(), checkpoint=initial,
                  branches=branches, prefix_audit=branch_audit(prefix_schedule(), np.zeros(4)),
                  wall_ns=time.perf_counter_ns()-began, peak_rss_bytes=peak_rss_bytes()))
        return dict(status='complete', network_id=n, replicate_id=rep, wall_ns=time.perf_counter_ns()-began)
    except Exception as e:
        if 'results' in locals() and results:
            _save_npz(folder/'partial.npz', **arrays(results))
        record = dict(status='failed', network_id=n, replicate_id=rep, error=f'{type(e).__name__}: {e}')
        save_json(folder/'failure.json', record); return record
    finally:
        if engine is not None: engine.close()
        del engine; gc.collect()


def _check_worker(deadline_ns):
    Deadline.from_environment(deadline_ns).check()
    stop = os.environ.get('NEUROMANCER_STOP_FILE')
    if stop and Path(stop).exists():
        raise TimeoutError('Supervisor requested cooperative stop')


def main():
    began_ns = now_ns()
    p = argparse.ArgumentParser(); p.add_argument('--stage', choices=('TUNE', 'CONFIRM'), required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--selection', type=Path); args = p.parse_args()
    names = ('ZERO', 'FIXED', 'MAX', *GAINS)
    reps = (40,); limit = 3600
    if args.stage == 'CONFIRM':
        if args.selection is None: raise SystemExit('Committed selection required')
        selection = json.loads(args.selection.read_text()); assert selection['frozen']
        names = ('ZERO', 'FIXED', 'MAX', selection['controller']); reps = (41, 42); limit = 5400
    stage_end = began_ns + int(limit*1e9)
    deadline = (Deadline.from_environment() if 'NEUROMANCER_DEADLINE_NS' in os.environ
                else Deadline(stage_end, clock_domain()))
    if deadline.end_ns > stage_end:
        raise ValueError('Inherited deadline exceeds the frozen stage cap')
    args.output.mkdir(parents=True, exist_ok=False)
    record = provenance(); record.update(started_epoch_s=time.time(), started_monotonic_ns=began_ns,
        deadline_monotonic_ns=deadline.end_ns, deadline_clock_id=deadline.clock_id, worker_performance_clock='perf_counter_ns: system uptime, excludes suspension on macOS', stage=args.stage, names=names, replicates=reps,
        networks=list(range(10)), wall_limit_s=limit,
        simulated_seconds=(51+32*2*len(names))*10*len(reps),
        protocol_sha256=hashlib.sha256(Path('docs/research/009_M005A_CONTROL_PROTOCOL.md').read_bytes()).hexdigest())
    if args.selection: record['selection_sha256'] = hashlib.sha256(args.selection.read_bytes()).hexdigest()
    atomic_json(args.output/'provenance.json', record)
    commands = [[sys.executable, '-m', 'neuromancer.control_experiment', '--worker',
                 str(n), str(rep), str(args.output.resolve()), json.dumps(names), str(deadline.end_ns)]
                for n in range(10) for rep in reps]
    result = supervise(commands, args.output/'supervision', deadline)
    if result['status'] != 'COMPLETED':
        atomic_json(args.output/'resource_stop.json', result)
        raise SystemExit('Acquisition did not qualify: ' + result['status'])
    deadline.check()
    trials = [json.loads((args.output/f'n{n}_r{rep}'/'trial.json').read_text())
              for n in range(10) for rep in reps]
    if any(t['status'] != 'complete' for t in trials):
        raise SystemExit('Incomplete acquisition')
    deadline.check()
    atomic_json(args.output/'summary.json', dict(status='complete', trials=trials,
                wall_ns=now_ns()-began_ns))
    try:
        deadline.check()
    except TimeoutError:
        atomic_json(args.output/'summary.json', dict(status='partial', reason='publication exceeded deadline'))
        raise


if __name__ == '__main__':
    if sys.argv[1:2] == ['--worker']:
        n, rep, output, names, deadline = sys.argv[2:]
        result = run_trial(int(n), int(rep), tuple(json.loads(names)), output, int(deadline))
        raise SystemExit(0 if result['status'] == 'complete' else 1)
    main()
