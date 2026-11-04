"""Instrumented synthetic failure paths; never a neural/scientific worker."""
import atexit
import errno
import json
import os
from pathlib import Path
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from supervisor_timing import WorkerTrace

mode, folder = sys.argv[1:3]
root = Path(folder)
trace = WorkerTrace(root)
clock = trace.clock
(root / "pid.json").write_text(json.dumps(dict(pid=os.getpid(), pgid=os.getpgrp())))
trace.event("imports_begin")
# Preserve the eager package-import stage as an observable diagnostic component.
from neuromancer.clocks import clock_domain
assert clock_domain() == trace.clock_id
trace.event("imports_completed")
(root / "partial.txt").write_text("completed checkpoint\n")


def shutdown():
    trace.event("shutdown_begin")
    if mode == "shutdown_delay":
        trace.event("shutdown_delay_begin", requested_s=1.2)
        time.sleep(1.2)
        trace.event("shutdown_delay_end")
    trace.event("shutdown_end")


def display_exception(kind, value, frames):
    trace.event("exception_hook_begin", exception_type=kind.__name__)
    trace.event("traceback_format_begin")
    if mode == "traceback_delay":
        trace.event("traceback_delay_begin", requested_s=1.2)
        time.sleep(1.2)
        trace.event("traceback_delay_end")
    text = "".join(traceback.format_exception(kind, value, frames))
    trace.event("traceback_format_end", characters=len(text))
    trace.event("stderr_write_begin")
    sys.stderr.write(text)
    trace.event("stderr_write_end")
    trace.event("stderr_flush_begin")
    sys.stderr.flush()
    trace.event("stderr_flush_end")
    trace.event("exception_hook_end")


atexit.register(shutdown)
sys.excepthook = display_exception
if mode == "normal_exit":
    trace.event("normal_exit_intent")
    sys.exit(0)

trace.event("failure_operation_begin")
if mode == "operation_delay":
    trace.event("operation_delay_begin", requested_s=1.2)
    time.sleep(1.2)
    trace.event("operation_delay_end")
try:
    if mode == "python_exception":
        failure = RuntimeError("deliberate pure-Python failure")
        trace.event("exception_created", exception_type=type(failure).__name__)
        raise failure
    (root / "partial.txt" / "impossible").write_text("must not publish")
except (OSError, RuntimeError) as failure:
    # For OSError, creation occurred between operation_begin and this observation.
    trace.event("exception_caught", exception_type=type(failure).__name__,
                errno=getattr(failure, "errno", None))
    if mode in ("caught_exit", "shutdown_delay"):
        assert isinstance(failure, NotADirectoryError) and failure.errno == errno.ENOTDIR
        report = dict(exception_type=type(failure).__name__, errno=failure.errno,
                      clock_id=trace.clock_id, scientific_success=False)
        trace.event("failure_record_begin")
        (root / "failure.json").write_text(json.dumps(report))
        trace.event("failure_record_end")
        trace.event("nonzero_exit_intent", code=23)
        if mode == "caught_exit":
            os._exit(23)
        sys.exit(23)
    trace.event("exception_propagating")
    raise
else:
    raise AssertionError("Deliberate failed publication unexpectedly succeeded")
