"""Synthetic workers only; run by test_supervisor under an outer watchdog."""
import sys as _sys
import os as _os
from supervisor_timing import WorkerTrace
_trace=WorkerTrace(_sys.argv[2],_os.environ.get('M008_WORKER_TRACE')=='1')
_trace.event('imports_begin')
if _os.environ.get('M008_PREIMPORT_DELAY_S'):
    import time as _time
    _trace.event('preimport_delay_begin')
    _time.sleep(float(_os.environ['M008_PREIMPORT_DELAY_S']))
    _trace.event('preimport_delay_end')
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from neuromancer.clocks import now_ns, clock_domain
assert os.environ['NEUROMANCER_DEADLINE_CLOCK']==clock_domain()
_trace.event('imports_completed')
import atexit
atexit.register(lambda:_trace.event('worker_atexit'))

mode, folder = sys.argv[1:3]
p = Path(folder); p.mkdir(exist_ok=True)
# Cancellation can interrupt a write, so expose the PID marker only when complete.
pid_path = p / 'pid.json'
staged_pid = p / 'pid.json.tmp'
staged_pid.write_text(json.dumps({
    'pid': os.getpid(), 'pgid': os.getpgrp(),
    'deadline_ns': int(os.environ['NEUROMANCER_DEADLINE_NS']),
    'started_ns': now_ns(),
}))
staged_pid.replace(pid_path)
if mode in ('ignore_term', 'descendant', 'shutdown_block'):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
(p/'partial.txt').write_text('completed checkpoint\n')
if mode == 'complete':
    pass
elif mode == 'before':
    cutoff = int(sys.argv[3]); delay = (cutoff-now_ns())/1e9-.2
    _trace.event('sleep_request',requested_s=max(0.,delay),nominal_target_ns=cutoff-200000000)
    if delay > 0: time.sleep(delay)
    _trace.event('sleep_wake')
    if os.environ.get('M008_WAKE_DELAY_S'):
        _trace.event('wake_delay_begin');time.sleep(float(os.environ['M008_WAKE_DELAY_S']));_trace.event('wake_delay_end')
elif mode == 'race':
    cutoff = int(sys.argv[3]); delay = (cutoff-now_ns())/1e9
    if delay > 0: time.sleep(delay)
elif mode == 'exception':
    raise RuntimeError('injected worker exception')
elif mode == 'unexpected':
    os._exit(17)
elif mode == 'write_failure':
    # Final artifact cannot be published; earlier checkpoint must survive.
    (p/'partial.txt'/'impossible').write_text('fail')
elif mode in ('descendant', 'orphan'):
    child = subprocess.Popen([sys.executable, __file__, 'ignore_term', str(p/'child')])
    (p/'child_pid.json').write_text(json.dumps({'pid':child.pid}))
    if mode == 'orphan':
        # Wait until descendant has installed its handler before leader exits.
        while not (p/'child'/'partial.txt').exists(): time.sleep(.005)
        sys.exit(0)
    # Reap our descendant on TERM; KILL only after child reaped. This worker
    # resists cooperative cancellation but owns/reaps its child correctly.
    def terminate(sig, frame):
        child.kill(); child.wait(timeout=.1); sys.exit(0)
    signal.signal(signal.SIGTERM, terminate)
    while True: time.sleep(.01)
elif mode == 'cooperative':
    while not Path(os.environ['NEUROMANCER_STOP_FILE']).exists(): time.sleep(.005)
elif mode == 'shutdown_block':
    while not Path(os.environ['NEUROMANCER_STOP_FILE']).exists(): time.sleep(.005)
    while True: time.sleep(60)
else:  # timeout, ignore_stop and ignore_term
    time.sleep(60)

_trace.event('completion_intent')
if _trace.enabled:
    (p/'completion.json').write_text(json.dumps(dict(clock_id=clock_domain(),intent_ns=now_ns())))
    _trace.event('completion_record_written')
