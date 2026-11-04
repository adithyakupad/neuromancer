"""Real failed publication plus explicit nonzero exit; fixture use only."""
import errno
import json
import os
from pathlib import Path
import sys
import time

from supervisor_timing import WorkerTrace

root = Path(sys.argv[1])
mode = sys.argv[2]
if mode not in ("timely", "late"):
    raise ValueError("Unknown failure-fixture mode")
trace = WorkerTrace(root)
clock = trace.clock
deadline = int(os.environ["NEUROMANCER_DEADLINE_NS"])


def publish(name, value):
    # Close the file before replace/_exit: no Python buffer is left to flush.
    temporary = root / (name + ".tmp")
    temporary.write_text(json.dumps(value))
    os.replace(temporary, root / name)


publish("pid.json", dict(pid=os.getpid(), pgid=os.getpgrp(), deadline_ns=deadline))
(root / "partial.txt").write_text("completed checkpoint\n")
ready = trace.event("ready")
publish("ready.json", dict(clock_id=trace.clock_id, ready_ns=ready))
while not (root / "release.json").exists():
    if clock.now_ns() >= deadline:
        raise TimeoutError("No release before original deadline")
    time.sleep(.001)
release = json.loads((root / "release.json").read_text())
assert release["clock_id"] == trace.clock_id
trace.event("release_seen", released_ns=release["released_ns"])

operation = trace.event("failure_operation_begin")
try:
    (root / "partial.txt" / "impossible").write_text("must not publish")
except NotADirectoryError as failure:
    assert failure.errno == errno.ENOTDIR
    caught = trace.event("exception_caught", exception_type=type(failure).__name__,
                         errno=failure.errno)
    publish("failure.json", dict(clock_id=trace.clock_id, operation_ns=operation,
                                caught_ns=caught, exception_type=type(failure).__name__,
                                errno=failure.errno, scientific_success=False))
    trace.event("failure_record_written")
else:
    raise AssertionError("Artifact publication unexpectedly succeeded")

if mode == "late":
    trace.event("late_failure_wait")
    # Deliberately remain alive after reporting the failure. TERM still applies;
    # this absolute bound also prevents an orphan fixture from waiting forever.
    while clock.now_ns() < deadline:
        time.sleep(.005)
trace.event("failure_exit_intent", code=23)
os._exit(23)
