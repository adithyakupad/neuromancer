"""Stdlib-only readiness fixture for phase-specific clock qualification."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from supervisor_timing import WorkerTrace


folder = Path(sys.argv[1])
mode = sys.argv[2]
trace = WorkerTrace(folder)
clock = trace.clock
signal.signal(signal.SIGTERM, signal.SIG_IGN)


def publish(name, value):
    path = folder/name
    staged = path.with_name(path.name+'.tmp')
    with staged.open('w') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(staged, path)


publish('pid.json', json.dumps(dict(pid=os.getpid(), pgid=os.getpgrp(),
        deadline_ns=int(os.environ['NEUROMANCER_DEADLINE_NS']), started_ns=clock.now_ns())))
publish('partial.txt', 'completed checkpoint\n')
if mode == 'descendant':
    child = subprocess.Popen([sys.executable, __file__, str(folder/'child'), 'ignore_term'])

    def terminate(sig, frame):
        child.kill()
        child.wait(timeout=.1)
        sys.exit(0)

    signal.signal(signal.SIGTERM, terminate)
    while not (folder/'child/ready.json').exists():
        if clock.now_ns() >= int(os.environ['NEUROMANCER_DEADLINE_NS']):
            raise TimeoutError('Descendant readiness missed original deadline')
        time.sleep(.001)
publish('ready.json', json.dumps(dict(clock_id=trace.clock_id, ready_ns=clock.now_ns())))
while True:
    time.sleep(.01)
