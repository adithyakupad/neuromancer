"""One fixture-only persistence observation; production source is not edited."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import threading
import time

import neuromancer.supervisor as supervisor
from neuromancer.clocks import now_ns

resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
root = Path(sys.argv[1])
condition = sys.argv[2]
deadline = supervisor.Deadline.after(1.8)
cutoff = deadline.end_ns - 800_000_000
original = supervisor.atomic_json
events = []
chunks = []
initial_seen = False
dropped = 0
os.set_blocking(sys.stdout.fileno(), False)


def stamp(kind, pipe=True, **fields):
    global dropped
    usage = resource.getrusage(resource.RUSAGE_SELF)
    row = dict(sequence=len(events), kind=kind, clock_id=deadline.clock_id,
               ns=now_ns(), cpu_ns=time.process_time_ns(), voluntary=usage.ru_nvcsw,
               involuntary=usage.ru_nivcsw, **fields)
    events.append(row)
    if pipe:
        try:
            # Stage markers only: chunk-level events stay in memory to avoid
            # filling the pipe or performing diagnostic disk I/O while measuring.
            os.write(sys.stdout.fileno(), (json.dumps(row) + "\n").encode())
        except BlockingIOError:
            dropped += 1


def delay(stage):
    if condition == stage + "_delay":
        stamp(stage + "_injected_delay_begin", seconds=1.05)
        time.sleep(1.05)
        stamp(stage + "_injected_delay_end")


class ObservedWriter:
    def __init__(self, stream):
        self.stream = stream

    def write(self, value):
        stamp("write_begin", pipe=False, characters=len(value))
        result = self.stream.write(value)
        stamp("write_end", pipe=False)
        chunks.append(value)
        return result


def observed_atomic(path, value):
    global initial_seen
    if path.name != "progress.json" or initial_seen:
        return original(path, value)
    initial_seen = True
    stamp("initial_publication_begin")
    temporary = path.with_name(path.name + ".tmp")
    stamp("file_create_begin")
    with temporary.open("w") as stream:
        stamp("file_create_end")
        delay("serialization")
        stamp("serialization_with_writes_begin")
        delay("write")
        # Same encoder/options and write chunks as production json.dump. Pure
        # serialization is interleaved with writes; report both, not a fake split.
        json.dump(value, ObservedWriter(stream), allow_nan=False, indent=2)
        stamp("serialization_with_writes_end")
        delay("flush")
        stamp("flush_begin")
        stream.flush()
        stamp("flush_end")
        delay("fsync")
        stamp("fsync_begin")
        os.fsync(stream.fileno())
        stamp("fsync_end")
        stamp("close_begin")
    stamp("close_end")
    delay("replace")
    stamp("replace_begin")
    os.replace(temporary, path)
    stamp("replace_end")
    stamp("publication_return")


errors = []


def release():
    try:
        ready = root / "worker/ready.json"
        while now_ns() < cutoff:
            if ready.exists():
                record = json.loads(ready.read_text())
                assert record["clock_id"] == deadline.clock_id
                original(root / "worker/release.json",
                         dict(clock_id=deadline.clock_id, released_ns=now_ns()))
                return
            time.sleep(.001)
        errors.append("No verified release before original cutoff")
    except Exception as error:
        errors.append(repr(error))


supervisor.atomic_json = observed_atomic
thread = threading.Thread(target=release, daemon=True)
thread.start()
command = [sys.executable, "tests/supervisor_failure_worker.py", str(root / "worker"), "timely"]
result = supervisor.supervise([command], root / "supervision", deadline, trace=True)
thread.join(timeout=.1)
stamp("returned_to_caller")
text = "".join(chunks)
assert json.dumps(json.loads(text), allow_nan=False, indent=2) == text
(root / "initial_payload.json").write_text(text)
original(root / "component_events.json", events)
original(root / "returned.json", result)
original(root / "observer.json", dict(dropped_stage_events=dropped, errors=errors,
    thread_alive=thread.is_alive(), initial_payload_sha256=hashlib.sha256(text.encode()).hexdigest(),
    json_dump_options=dict(allow_nan=False, indent=2), measured_fsync_calls=1,
    child_peak_rss_native=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))
rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
rss_bytes = rss if sys.platform == "darwin" else rss * 1024
assert rss_bytes <= 1024**3
assert not dropped and not thread.is_alive() and result["cleanup_verified"]
if condition != "ordinary":
    assert result["status"] == "DEADLINE_EXCEEDED"
else:
    assert result["status"] in ("WORKER_FAILURE", "DEADLINE_EXCEEDED")
assert not any(row["terminal"] == "COMPLETED" for row in result["workers"])
