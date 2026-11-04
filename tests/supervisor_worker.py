"""Synthetic workers only; run by test_supervisor under an outer watchdog."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from neuromancer.clocks import now_ns, clock_domain
assert os.environ['NEUROMANCER_DEADLINE_CLOCK']==clock_domain()

mode, folder = sys.argv[1:3]
p = Path(folder); p.mkdir(exist_ok=True)
(p/'pid.json').write_text(json.dumps({'pid':os.getpid(), 'pgid':os.getpgrp(), 'deadline_ns':int(os.environ['NEUROMANCER_DEADLINE_NS']), 'started_ns':now_ns()}))
if mode in ('ignore_term', 'descendant', 'shutdown_block'):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
(p/'partial.txt').write_text('completed checkpoint\n')
if mode == 'complete':
    pass
elif mode == 'before':
    cutoff = int(sys.argv[3]); delay = (cutoff-now_ns())/1e9-.2
    if delay > 0: time.sleep(delay)
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
