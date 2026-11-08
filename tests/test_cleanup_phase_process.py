"""A1 real cancellation-phase failure control, with separate post-result reaping."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


DRIVER = '''
import json,os,signal,sys,time
from pathlib import Path
import neuromancer.supervisor as s
p=Path(sys.argv[1]);native=s.now_ns;offset=0;triggered=None
outer_end=time.monotonic()+5
def injected():
 global offset,triggered
 if triggered is None and (p/'supervision/stop-0').exists():
  triggered=native();offset=10000000000
 return native()+offset
s.now_ns=injected
d=s.Deadline.after(1.8)
r=s.supervise([[sys.executable,sys.argv[2],str(p/'worker'),'ignore_term']],p/'supervision',d)
(p/'returned.json').write_text(json.dumps(r))
late_reaped=False;permission_errors=[]
pid=r['workers'][0].get('pid')
while pid and time.monotonic()<outer_end:
 try:
  reaped,_=os.waitpid(pid,os.WNOHANG)
  late_reaped=late_reaped or reaped==pid
 except ChildProcessError:pass
 try:os.killpg(pid,0)
 except ProcessLookupError:break
 except PermissionError as exc:permission_errors.append(repr(exc))
 time.sleep(.001)
else:
 if pid:raise RuntimeError('Independent observer could not verify group absence')
(p/'observer.json').write_text(json.dumps(dict(triggered_ns=triggered,late_reaped=late_reaped,
 observed_trial_status=r['status'],verified_before_cleanup_end=r['finished_ns']<=r['cleanup_deadline_ns'],
 group_absent=True,permission_errors=permission_errors,original_deadline_ns=d.end_ns)))
'''


def test_real_clock_jump_during_cancellation_retains_failure(tmp_path):
    worker = Path(__file__).with_name('supervisor_phase_worker.py')
    process = subprocess.Popen([sys.executable, '-c', DRIVER, str(tmp_path), str(worker)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        for marker in tmp_path.rglob('pid.json'):
            try:
                os.killpg(json.loads(marker.read_text())['pgid'], signal.SIGKILL)
            except ProcessLookupError:
                pass
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=1)
        raise AssertionError('Independent outer watchdog intervened')
    (tmp_path/'stdout.log').write_bytes(stdout)
    (tmp_path/'stderr.log').write_bytes(stderr)
    if process.returncode != 0:
        cleanup = []
        for marker in tmp_path.rglob('pid.json'):
            group = json.loads(marker.read_text())['pgid']
            try:
                os.killpg(group, signal.SIGKILL)
                cleanup.append(dict(pgid=group, action='emergency KILL after observer failure'))
            except ProcessLookupError:
                cleanup.append(dict(pgid=group, action='already absent'))
            except PermissionError as exc:
                cleanup.append(dict(pgid=group, action='cleanup denied', error=repr(exc)))
        (tmp_path/'observer-failure-cleanup.json').write_text(json.dumps(cleanup, indent=2))
    assert process.returncode == 0, stderr.decode()
    result = json.loads((tmp_path/'returned.json').read_text())
    observed = json.loads((tmp_path/'observer.json').read_text())
    assert observed['triggered_ns'] is not None and observed['group_absent']
    assert not observed['verified_before_cleanup_end']
    assert result['status'] in ('CLEANUP_FAILURE', 'DEADLINE_EXCEEDED')
    assert result['cause'] == 'DEADLINE_EXCEEDED'
    assert (tmp_path/'worker/partial.txt').read_text() == 'completed checkpoint\n'
    assert observed['observed_trial_status'] == result['status']
