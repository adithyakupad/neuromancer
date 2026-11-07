"""Capture the unchanged qualified acquisition CLI; no scientific definitions here."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from neuromancer.supervisor import atomic_json

ROOT=Path(__file__).resolve().parent


def main():
    selection=ROOT/'tuning_analysis/selection.json'
    seal=json.loads((ROOT/'selection_freeze.json').read_text())
    assert hashlib.sha256(selection.read_bytes()).hexdigest()==seal['selection_sha256']
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','status','--porcelain'],text=True).strip()==''
    # The current clean commit must contain the frozen selection, not just a file.
    assert subprocess.check_output(['git','show',head+':reports/evidence/m005a_3/tuning_analysis/selection.json'])==selection.read_bytes()
    raw=ROOT/'confirmation'
    assert not raw.exists()
    command=[sys.executable,'-m','neuromancer.control_experiment','--stage','CONFIRM',
             '--output',str(raw),'--selection',str(selection)]
    begin=time.monotonic_ns();epoch=time.time();reason=None
    with (ROOT/'acquisition.log').open('wb') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        awake=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(proc.pid)])
        atomic_json(ROOT/'acquisition_launch.json',dict(pid=proc.pid,command=command,head=head,
                    selection_sha256=seal['selection_sha256'],started_epoch_s=epoch,started_monotonic_ns=begin))
        try:
            # Cleanup-only outer safety net. Beyond5400s can NEVER qualify.
            code=proc.wait(timeout=5405)
        except subprocess.TimeoutExpired:
            reason='external safety watchdog; acquisition resource failure'
            progress=raw/'supervision/progress.json'
            if progress.exists():
                for worker in json.loads(progress.read_text())['workers']:
                    if worker.get('pgid'):
                        try:os.killpg(worker['pgid'],signal.SIGKILL)
                        except ProcessLookupError:pass
            os.killpg(proc.pid,signal.SIGKILL);code=proc.wait(timeout=1)
        finally:
            awake.terminate()
            try:awake.wait(timeout=1)
            except subprocess.TimeoutExpired:awake.kill();awake.wait(timeout=1)
    finish=time.monotonic_ns();end=time.time()
    path=raw/'summary.json'
    record=dict(returncode=code,reason=reason,started_epoch_s=epoch,finished_epoch_s=end,
                calendar_duration_s=end-epoch,monotonic_duration_s=(finish-begin)/1e9,
                summary_sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                source_revision=head,command=command,selection_sha256=seal['selection_sha256'])
    record['status']='COMPLETE' if code==0 and reason is None and 0<=end-epoch<=5400 and (finish-begin)/1e9<=5400 and path.exists() else 'PARTIAL'
    atomic_json(ROOT/'acquisition_closure.json',record)
    print(json.dumps(record),flush=True)
    if record['status']!='COMPLETE':sys.exit(1)


if __name__=='__main__':main()
