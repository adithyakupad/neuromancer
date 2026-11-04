"""Independent watchdog recording only owned fixture process information."""
import json
import os
from pathlib import Path
import signal
import subprocess
from supervisor_timing import load_clock


def communicate(process, root, *, timeout=6):
    clock=load_clock();began=clock.now_ns();intervened=False;out=b'';err=b''
    try:
        out,err=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        intervened=True
        groups={process.pid}
        for f in Path(root).rglob('pid.json'):
            if not f.is_symlink():groups.add(json.loads(f.read_text())['pgid'])
        for group in groups:
            try:os.killpg(group,signal.SIGKILL)
            except ProcessLookupError:pass
        out,err=process.communicate(timeout=1)
    finally:
        record=dict(clock_id=clock.clock_domain(),started_ns=began,finished_ns=clock.now_ns(),outer_timeout_s=timeout,watchdog_intervened=intervened,supervisor_pid=process.pid,returncode=process.returncode)
        (Path(root)/'outer_watchdog.json').write_text(json.dumps(record,indent=2)+'\n')
        (Path(root)/'outer_stdout.log').write_bytes(out);(Path(root)/'outer_stderr.log').write_bytes(err)
    if intervened:raise AssertionError('Independent outer watchdog intervened')
    return out,err
