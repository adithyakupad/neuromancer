"""Bounded POSIX command supervision. No neural or controller dependencies."""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Sequence


@dataclass(frozen=True)
class Deadline:
    end_ns: int

    @classmethod
    def after(cls, seconds: float) -> 'Deadline':
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('Positive finite budget required')
        return cls(time.monotonic_ns() + int(seconds * 1e9))

    def remaining(self) -> float:
        return max(0., (self.end_ns - time.monotonic_ns()) / 1e9)

    def check(self) -> None:
        if time.monotonic_ns() >= self.end_ns:
            raise TimeoutError('Monotonic global deadline exceeded')


def atomic_json(path: Path, value: object) -> None:
    """Durable completed artifact; interrupted writes retain the previous version."""
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, allow_nan=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # Cannot prove cleanup, including an OS-owned orphan zombie.


def _signal(pgid: int, sig: int) -> str | None:
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        return repr(exc)


def supervise(commands: Sequence[Sequence[str]], output: Path, deadline: Deadline,
              *, workers: int = 3, cooperative_s: float = .2,
              terminate_s: float = .2, reap_s: float = .4) -> dict:
    """All startup, jobs and cleanup share deadline; no deadline is reset here.

    Workers inherit NEUROMANCER_STOP_FILE for cooperative cancellation and
    NEUROMANCER_DEADLINE_NS for the *same* absolute monotonic deadline.
    Only trusted POSIX children that do not escape their process group supported.
    """
    if os.name != 'posix':
        raise NotImplementedError('POSIX process groups required')
    if workers < 1 or any(not math.isfinite(s) or s <= 0 for s in
                          (cooperative_s, terminate_s, reap_s)):
        raise ValueError('Positive worker count and grace periods required')
    started = time.monotonic_ns()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    reserve_ns = int((cooperative_s + terminate_s + reap_s)*1e9)
    work_end = deadline.end_ns - reserve_ns
    publication_ns = min(20_000_000, int(reap_s*1e9/2))
    records = [dict(index=i, command=list(c), state='CREATED', events=[dict(state='CREATED', monotonic_ns=started)],
                    terminal=None, cause=None) for i, c in enumerate(commands)]
    active: dict[int, subprocess.Popen] = {}
    handles = []
    cause = None
    error = None
    persistence_errors = []

    def event(r, state):
        r['state'] = state
        r['events'].append(dict(state=state, monotonic_ns=time.monotonic_ns()))

    def persist():
        # Failure to persist never bypasses process cleanup.
        try:
            atomic_json(output/'progress.json', dict(cause=cause, workers=records))
        except Exception as exc:
            persistence_errors.append(repr(exc))
            raise

    def poll():
        for i, proc in list(active.items()):
            code = proc.poll()  # waitpid(WNOHANG): reaps only our direct child.
            if code is not None:
                r = records[i]
                r['returncode'] = code
                r['parent_reaped'] = True
                # A leader's exit says nothing about its descendants.
                if not group_exists(proc.pid):
                    event(r, 'REAPED')
                    r['terminal'] = 'COMPLETED' if code == 0 else 'WORKER_FAILURE'
                    r['cause'] = cause or ('normal exit' if code == 0 else f'exit {code}')
                    del active[i]

    def pause_until(end_ns):
        while active and time.monotonic_ns() < end_ns:
            poll()
            time.sleep(min(.01, max(0., (end_ns-time.monotonic_ns())/1e9)))

    try:
        persist()
        next_job = 0
        while next_job < len(records) or active:
            if time.monotonic_ns() >= work_end:
                cause = 'DEADLINE_EXCEEDED'
                break
            poll()
            failed = [r for r in records if r['terminal'] == 'WORKER_FAILURE']
            # A successful leader leaving a descendant is also a worker failure.
            orphaned = [i for i,p in active.items() if p.returncode is not None]
            if failed or orphaned:
                cause = 'WORKER_FAILURE'
                break
            while next_job < len(records) and len(active) < workers:
                if time.monotonic_ns() >= work_end:
                    break
                i = next_job; r = records[i]
                stop_file = output/f'stop-{i}'
                env = dict(os.environ, NEUROMANCER_STOP_FILE=str(stop_file),
                           NEUROMANCER_DEADLINE_NS=str(deadline.end_ns))
                log = (output/f'worker-{i}.log').open('wb'); handles.append(log)
                proc = subprocess.Popen(r['command'], stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                active[i] = proc
                r.update(pid=proc.pid, pgid=proc.pid, stop_file=str(stop_file))
                event(r, 'RUNNING'); next_job += 1
                persist()
            if time.monotonic_ns() >= work_end:
                cause = 'DEADLINE_EXCEEDED'
                break
            if not active and next_job == len(records):
                break
            time.sleep(min(.01, max(0., (work_end-time.monotonic_ns())/1e9)))
        # Completion observed after cutoff is conservatively non-success.
        if time.monotonic_ns() >= work_end:
            cause = 'DEADLINE_EXCEEDED'
    except BaseException as exc:
        cause = 'SUPERVISOR_FAILURE'
        error = repr(exc)
    finally:
        # Grace windows are clamped to the original hard deadline. They never
        # receive a fresh global budget, including on early worker failures.
        try:
            if active:
                for i in active:
                    event(records[i], 'STOP_REQUESTED')
                    try:
                        Path(records[i]['stop_file']).touch(exist_ok=False)
                    except OSError as exc:
                        persistence_errors.append(repr(exc))
                pause_until(min(deadline.end_ns-int((terminate_s+reap_s)*1e9),
                                time.monotonic_ns()+int(cooperative_s*1e9)))
                for i, proc in active.items():
                    event(records[i], 'TERMINATING')
                    records[i].setdefault('signal_errors', []).append(_signal(proc.pid, signal.SIGTERM))
                pause_until(min(deadline.end_ns-int(reap_s*1e9),
                                time.monotonic_ns()+int(terminate_s*1e9)))
                for i, proc in active.items():
                    event(records[i], 'KILLING')
                    records[i].setdefault('signal_errors', []).append(_signal(proc.pid, signal.SIGKILL))
                pause_until(min(deadline.end_ns-publication_ns, time.monotonic_ns()+int(reap_s*1e9)))
                poll()
        except BaseException as exc:
            cause = 'SUPERVISOR_FAILURE'
            error = repr(exc)
            # Best-effort emergency kill; never an unbounded wait.
            for proc in active.values():
                _signal(proc.pid, signal.SIGKILL)
        for log in handles:
            log.close()

    if active:
        status = 'CLEANUP_FAILURE'
    elif cause:
        status = cause
    elif persistence_errors:
        status = 'SUPERVISOR_FAILURE'
    elif time.monotonic_ns() >= work_end:
        status = cause = 'DEADLINE_EXCEEDED'
    else:
        status = 'COMPLETED'
    for r in records:
        if cause and r['events'] and any(e['state'] == 'STOP_REQUESTED' for e in r['events']):
            r['cause'] = cause
        if r['terminal'] is None:
            r['terminal'] = ('CLEANUP_FAILURE' if r['index'] in active else
                             'NOT_STARTED')
            r['cause'] = cause or status
        elif cause and r['events'] and any(e['state'] == 'STOP_REQUESTED' for e in r['events']):
            r['terminal'] = ('FORCED_TERMINATION' if any(e['state'] in ('TERMINATING','KILLING')
                               for e in r['events']) else cause)
            r['cause'] = cause
    result = dict(status=status, cause=cause or 'normal completion', error=error, workers=records,
                  started_ns=started, deadline_ns=deadline.end_ns,
                  work_cutoff_ns=work_end, finished_ns=time.monotonic_ns(),
                  persistence_errors=persistence_errors,
                  cleanup_verified=not active)
    # Progress retains evidence if this final write fails. Never return success.
    try:
        atomic_json(output/'terminal.json', result)
    except Exception as exc:
        result.update(status='SUPERVISOR_FAILURE', cause='terminal artifact write failed', error=repr(exc))
        persistence_errors.append(repr(exc))
        print(json.dumps(result), file=sys.stderr, flush=True)
        return result
    if time.monotonic_ns() >= deadline.end_ns and result['status'] == 'COMPLETED':
        result.update(status='DEADLINE_EXCEEDED', cause='terminal publication exceeded deadline')
        atomic_json(output/'terminal.json', result)
    return result
