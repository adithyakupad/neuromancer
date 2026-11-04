"""Non-neural adversarial probe of the unchanged production acquisition guard."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace


def worker(n, rep, names, output, deadline):
    folder = Path(output)/f'n{n}_r{rep}'
    folder.mkdir()
    (folder/'pid.json').write_text(json.dumps({'pid': os.getpid()}))
    if n == 0:
        return {'status': 'complete', 'network_id': n}
    if os.environ['PROBE_RESIST'] == '1':
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    (folder/'partial.txt').write_text('durable fixture checkpoint; not neural data')
    time.sleep(60)
    return {'status': 'complete', 'network_id': n}


def child(output):
    import neuromancer.control_experiment as ce
    started = time.monotonic()
    # Force the production parent's deadline path without waiting an hour.
    def clock():
        return time.time() + (3601 if time.monotonic()-started > 2 else 0)
    ce.time = SimpleNamespace(time=clock, perf_counter_ns=time.perf_counter_ns)
    ce.run_trial = worker
    ce.provenance = lambda: {'fixture': True}
    sys.argv = ['probe', '--stage', 'TUNE', '--output', output]
    ce.main()


def run(root):
    import neuromancer.control_experiment as ce
    root.mkdir(exist_ok=False)
    records = []
    for resistant in (False, True):
        output = root/('resistant' if resistant else 'cooperative')
        env = dict(os.environ, PROBE_RESIST=str(int(resistant)))
        began = time.monotonic()
        p = subprocess.Popen([sys.executable, __file__, 'child', str(output)], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        watchdog = False
        try:
            log, _ = p.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            watchdog = True
            os.killpg(p.pid, signal.SIGKILL)
            log, _ = p.communicate()
        elapsed = time.monotonic()-began
        (root/f'{output.name}.log').write_bytes(log)
        pids = [json.loads(f.read_text())['pid'] for f in output.glob('*/pid.json')]
        # Group kill above is external fixture cleanup, never production success.
        records.append(dict(case=output.name, elapsed_s=elapsed, returncode=p.returncode,
                            external_watchdog_required=watchdog, worker_pids=pids,
                            resource_stop=json.loads((output/'resource_stop.json').read_text()),
                            summary_exists=(output/'summary.json').exists(),
                            persisted_partial_count=len(list(output.glob('*/partial.txt')))))
    # Explicit backward-clock counterexample: expired elapsed time is invisible.
    ce.check_deadline(100., 99.)
    result = {'cases': records, 'backward_epoch_counterexample_accepted': True,
              'scientific_acquisition': False, 'guard_qualified': False}
    assert not records[0]['external_watchdog_required']
    assert records[1]['external_watchdog_required']
    assert all(not r['summary_exists'] and r['returncode'] != 0 for r in records)
    # Restart is fail-closed: exclusive output creation prevents accidental overwrite.
    env = dict(os.environ, PROBE_RESIST='0')
    retry = subprocess.run([sys.executable, __file__, 'child', str(root/'cooperative')],
                           env=env, capture_output=True, timeout=8)
    result['restart_rejected'] = retry.returncode != 0 and b'FileExistsError' in retry.stderr
    assert result['restart_rejected']
    (root/'result.json').write_text(json.dumps(result, indent=2))


if __name__ == '__main__':
    if sys.argv[1] == 'child': child(sys.argv[2])
    else: run(Path(sys.argv[1]))
