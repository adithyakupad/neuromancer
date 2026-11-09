"""Independent archived branches under one unchanged stage deadline."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'reports/evidence/v1_finish/m005b/primary'
FILES = ('progress.json', 'checkpoints.jsonl', 'certificate.json', 'backend.json')
THREADS = ('VECLIB_MAXIMUM_THREADS', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def manifest():
    branches = []
    for network, replicate in read(ARCHIVE / 'provenance.json')['jobs']:
        trial = read(ARCHIVE / f'n{network}_r{replicate}' / 'trial.json')
        if (trial['network'], trial['replicate']) != (network, replicate):
            raise ValueError('Trial identity mismatch')
        for branch in trial['branches']:
            if branch['controller'] == 'RLS-MPC':
                if (branch['bins'], branch['plans']) != (3200, 64):
                    raise ValueError('Unexpected archived workload')
                branches.append([network, replicate, branch['name']])
    if len(branches) != 40 or len(set(map(tuple, branches))) != 40:
        raise ValueError('Invalid forty-branch manifest')
    return branches


def worker(output, branch, source):
    from neuromancer.clocks import now_ns
    from neuromancer.supervisor import Deadline, atomic_json
    from tools.m028_backend import bounds, driver, load_kernel
    from neuromancer.research_codec import model_digest

    deadline = Deadline.from_environment()
    started = now_ns()
    if head() != source:
        raise ValueError('Worker source differs')
    network, replicate, name = branch

    class BranchReader:
        """Narrow the two archive manifests in the isolated M028 driver."""
        dumps = staticmethod(json.dumps)

        @staticmethod
        def loads(value):
            data = json.loads(value)
            if isinstance(data, dict) and 'jobs' in data:
                if data['jobs'].count([network, replicate]) != 1:
                    raise ValueError('Worker trial is absent or duplicated')
                return {**data, 'jobs': [[network, replicate]]}
            if isinstance(data, dict) and 'branches' in data:
                selected = [b for b in data['branches'] if b['name'] == name]
                if len(selected) != 1 or selected[0]['controller'] != 'RLS-MPC':
                    raise ValueError('Worker branch is absent or duplicated')
                return {**data, 'branches': selected}
            return data

    if 'M029_KERNEL_DIR' in os.environ:
        from tools.m029_kernel import load as load_kernel
    kernel = load_kernel()
    module = bounds(kernel)
    replay = driver(module)
    replay.json = BranchReader
    trajectory = hashlib.sha256()

    class ObservedModel(replay._checked_model_type):
        def update(self, x, y, valid=True):
            super().update(x, y, valid)
            trajectory.update(model_digest(self))

    replay._checked_model_type = ObservedModel
    code = replay.run(output, 'first')
    atomic_json(output / 'backend.json', dict(denominators=replay.denominator_stats,
                query_cache=module.query_cache_stats))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    atomic_json(output / 'worker.json', dict(branch=branch, source=source,
                pid=os.getpid(), pgid=os.getpgrp(), deadline_ns=deadline.end_ns,
                clock_id=deadline.clock_id, started_ns=started, finished_ns=now_ns(),
                user_s=usage.ru_utime, system_s=usage.ru_stime,
                peak_rss_bytes=usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
                native_state_trajectory_sha256=trajectory.hexdigest(),
                kernel_sha256=sha(Path(kernel.__file__)), returncode=code,
                sha256={name: sha(output / name) for name in FILES}))
    deadline.check()
    return code


def verify_worker(output, branch, source, record, result, kernel_sha):
    from tools.m028_io import FORMAT, load_progress

    worker_record = read(output / 'worker.json')
    expected = dict(branch=branch, source=source, pid=record['pid'], pgid=record['pgid'],
                    deadline_ns=result['deadline_ns'], clock_id=result['deadline_clock_id'],
                    kernel_sha256=kernel_sha, returncode=0)
    for key, value in expected.items():
        if worker_record.get(key) != value:
            raise ValueError(f'Worker provenance differs for {branch} in {key}')
    if record['terminal'] != 'COMPLETED' or not record.get('parent_reaped'):
        raise ValueError(f'Worker did not reap successfully for {branch}')
    if not result['started_ns'] <= worker_record['started_ns'] <= worker_record['finished_ns'] < result['work_cutoff_ns']:
        raise ValueError(f'Worker timing outside the stage for {branch}')
    if {name: sha(output / name) for name in FILES} != worker_record['sha256']:
        raise ValueError(f'Worker artifact SHA-256 differs for {branch}')
    progress = load_progress(output / 'progress.json')
    certificate = read(output / 'certificate.json')
    denominator = read(output / 'backend.json')['denominators']
    lower = denominator['minimum_lower']
    if (progress.get('format') != FORMAT
            or (output / 'checkpoints.jsonl').stat().st_size != progress['ledger_bytes']
            or progress['completed_branches'] != 1
            or not certificate['stage_pass'] or certificate['failure'] is not None
            or certificate['completed_branches'] != 1 or certificate['prescribed_branches'] != 1
            or certificate['checkpoints'] != progress['checkpoints']
            or denominator != progress['positive_denominators']
            or denominator['count'] != 3200 or not math.isfinite(lower) or lower <= 0):
        raise ValueError(f'Incomplete branch certificate for {branch}')
    timings = certificate['timings']
    for name, count in [('information_update', 3200), ('native_update', 3200),
                        ('state_residual', 3200), ('digest', 3200), ('planner_certificate', 64)]:
        if timings[name]['calls'] != count:
            raise ValueError(f'Incomplete {name} for {branch}')
    checkpoints = progress['checkpoints']
    for row in checkpoints:
        if [row['network'], row['replicate'], row['branch']] != branch:
            raise ValueError(f'Wrong checkpoint identity for {branch}')
    if (len(checkpoints) != 65 or [r['step'] for r in checkpoints[:-1]] != list(range(0, 3200, 50))
            or checkpoints[-1].get('completed') is not True):
        raise ValueError(f'Incomplete or unordered checkpoint ledger for {branch}')
    numerical = {key: certificate[key] for key in ('maximum_coefficient_radius',
                 'maximum_covariance_radius', 'digest_differences')}
    numerical['checkpoints'] = checkpoints[:-1]
    numerical['denominators'] = denominator
    numerical['native_state_trajectory_sha256'] = worker_record['native_state_trajectory_sha256']
    fingerprint = hashlib.sha256(json.dumps(numerical, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return {**worker_record, 'numerical_sha256': fingerprint, 'updates': 3200, 'plans': 64,
            'timings': timings, 'startup_s': (worker_record['started_ns'] - next(
                e['monotonic_ns'] for e in record['events'] if e['state'] == 'RUNNING')) / 1e9}


def sample_rss(output, stop, rows, errors):
    from neuromancer.clocks import now_ns

    while not stop.is_set():
        try:
            path = output / 'supervision/progress.json'
            groups = {r['pgid'] for r in read(path)['workers'] if 'pgid' in r} if path.exists() else set()
            table = subprocess.check_output(['ps', '-axo', 'pid=,pgid=,rss='], text=True, timeout=2)
            processes = []
            for line in table.splitlines():
                pid, pgid, rss = map(int, line.split())
                if pid in {os.getpid(), os.getppid()} or pgid in groups:
                    processes.append([pid, pgid, rss * 1024])
            rows.append(dict(monotonic_ns=now_ns(), processes=processes,
                             rss_bytes=sum(row[2] for row in processes)))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            errors.append(repr(exc))
        stop.wait(1)


def coordinate(output, workers, size):
    from neuromancer.clocks import now_ns
    from neuromancer.supervisor import Deadline, atomic_json, group_exists, supervise

    deadline = Deadline.after(240 if size == 40 else 180)
    started = now_ns()
    source = head()
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT):
        raise ValueError('Qualification requires committed tracked sources')
    selected = manifest()[:size]
    variant = 'm029' if 'M029_KERNEL_DIR' in os.environ else 'm028'
    kernel_dir = Path(os.environ[variant.upper()+'_KERNEL_DIR'])
    binaries = list(kernel_dir.glob(variant+'_arithmetic*.so'))
    if len(binaries) != 1:
        raise ValueError('Expected one compiled kernel')
    kernel_sha = sha(binaries[0])
    commands = [[sys.executable, __file__, 'worker', str(output / f'branch-{i:02}'),
                 json.dumps(branch), source] for i, branch in enumerate(selected)]
    atomic_json(output / 'schedule.json', dict(source=source, branches=selected,
                workers=workers, deadline_ns=deadline.end_ns, kernel_sha256=kernel_sha,
                thread_env={key: os.environ.get(key) for key in THREADS}))
    rss, errors = [], []
    stop = threading.Event()
    sampler = threading.Thread(target=sample_rss, args=(output, stop, rss, errors), daemon=True)
    sampler.start()
    try:
        result = supervise(commands, output / 'supervision', deadline, workers=workers)
    finally:
        stop.set()
        sampler.join(timeout=2.1)
    atomic_json(output / 'supervisor-result.json', result)
    atomic_json(output / 'memory.json', dict(samples=rss, errors=errors))
    failure = None
    rows = []
    try:
        if (result['status'] != 'COMPLETED' or not result['cleanup_verified']
                or result['deadline_ns'] != deadline.end_ns or result['persistence_errors']
                or len(result['workers']) != size or sampler.is_alive() or not rss or errors):
            raise ValueError('Supervisor or resource observation failed qualification')
        if {p.name for p in output.glob('branch-*')} != {f'branch-{i:02}' for i in range(size)}:
            raise ValueError('Missing or unexpected branch output directories')
        for i, (branch, record) in enumerate(zip(selected, result['workers'], strict=True)):
            deadline.check()
            if record['index'] != i or record['command'] != commands[i] or group_exists(record['pgid']):
                raise ValueError(f'Worker ownership or cleanup mismatch for {branch}')
            rows.append(verify_worker(output / f'branch-{i:02}', branch, source, record, result, kernel_sha))
        if len({tuple(row['branch']) for row in rows}) != size:
            raise ValueError('Duplicate certified branch')
        deadline.check()
    except (OSError, ValueError, KeyError, TypeError, TimeoutError) as exc:
        failure = repr(exc)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    finished = now_ns()
    atomic_json(output / 'stage.json', dict(source=source, requested_branches=size, workers=workers,
                rows=rows, stage_pass=failure is None, failure=failure, release_qualified=False,
                wall_s=(finished-started)/1e9, worker_cpu_s=sum(r['user_s']+r['system_s'] for r in rows),
                coordinator_cpu_s=usage.ru_utime+usage.ru_stime,
                sampled_peak_process_tree_rss_bytes=max((r['rss_bytes'] for r in rss), default=None)))
    if failure is None:
        deadline.check()
    return int(failure is not None)


def launch(output, workers, size):
    from neuromancer.supervisor import atomic_json, group_exists

    output.mkdir(parents=True, exist_ok=False)
    budget = 240 if size == 40 else 180
    env = {**os.environ, **dict.fromkeys(THREADS, '1')}
    command = [sys.executable, __file__, 'coordinate', str(output), str(workers), str(size)]
    intervention = False
    survivors = []
    began = time.monotonic()
    cpu_before = sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2])
    with (output / 'launcher.log').open('wb') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True, env=env, cwd=ROOT)
        try:
            process.wait(timeout=budget + 5)
        except subprocess.TimeoutExpired:
            intervention = True
            groups = {process.pid}
            # Freeze the coordinator before reading its owned process groups.
            try:
                os.killpg(process.pid, signal.SIGSTOP)
            except ProcessLookupError:
                pass
            path = output / 'supervision/progress.json'
            if path.exists():
                groups.update(r['pgid'] for r in read(path)['workers']
                              if 'pgid' in r and r['state'] != 'REAPED')
            # Cover the window between Popen and the supervisor's first durable record.
            table = subprocess.check_output(['ps', '-axo', 'ppid=,pgid='], text=True, timeout=2)
            for line in table.splitlines():
                parent, pgid = map(int, line.split())
                if parent == process.pid:
                    groups.add(pgid)
            for pgid in groups:
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=2)
            survivors = sorted(g for g in groups if group_exists(g))
    atomic_json(output / 'launcher.json', dict(watchdog_intervened=intervention,
                surviving_groups=survivors, returncode=process.returncode,
                wall_s=time.monotonic()-began,
                total_child_cpu_s=sum(resource.getrusage(resource.RUSAGE_CHILDREN)[:2])-cpu_before))
    return int(intervention or process.returncode != 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['worker', 'coordinate', 'launch'])
    parser.add_argument('output', type=lambda value: Path(value).resolve())
    parser.add_argument('first')
    parser.add_argument('second')
    args = parser.parse_args()
    if args.mode == 'worker':
        sys.exit(worker(args.output, json.loads(args.first), args.second))
    workers, size = int(args.first), int(args.second)
    if workers not in (1, 2, 4) or size not in (8, 40):
        parser.error('Expected 1, 2 or 4 workers and 8 or 40 branches')
    sys.exit((coordinate if args.mode == 'coordinate' else launch)(args.output, workers, size))
