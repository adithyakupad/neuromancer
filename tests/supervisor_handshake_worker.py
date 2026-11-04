"""Immediate handshake worker: actual exit must still be observed before cutoff."""
import atexit
import json
import os
from pathlib import Path
import sys
import time
from supervisor_timing import WorkerTrace

p=Path(sys.argv[1]);trace=WorkerTrace(p);clock=trace.clock
trace.event('imports_completed')
(p/'pid.json').write_text(json.dumps(dict(pid=os.getpid(),pgid=os.getpgrp(),deadline_ns=int(os.environ['NEUROMANCER_DEADLINE_NS']),started_ns=clock.now_ns())))
(p/'partial.txt').write_text('completed checkpoint\n')
atexit.register(lambda:trace.event('worker_atexit'))
ready=trace.event('ready')
(p/'ready.tmp').write_text(json.dumps(dict(clock_id=trace.clock_id,ready_ns=ready)))
os.replace(p/'ready.tmp',p/'ready.json')
while not (p/'release.json').exists():
    if clock.now_ns()>=int(os.environ['NEUROMANCER_DEADLINE_NS']):raise TimeoutError('No release before original deadline')
    time.sleep(.001)
release=json.loads((p/'release.json').read_text());assert release['clock_id']==trace.clock_id
trace.event('release_seen',released_ns=release['released_ns'])
intent=trace.event('completion_intent')
(p/'completion.json').write_text(json.dumps(dict(clock_id=trace.clock_id,intent_ns=intent)))
trace.event('completion_record_written')
