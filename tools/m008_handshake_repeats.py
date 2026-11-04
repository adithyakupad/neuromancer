"""Frozen20 corrected handshake repetitions; original evidence remains separate."""
import hashlib,json,os,platform,resource,signal,subprocess,sys,time
from pathlib import Path
from neuromancer.supervisor import Deadline,atomic_json

def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);d=Deadline.after(900);rows=[]
 hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('src/neuromancer/supervisor.py','src/neuromancer/clocks.py','tests/test_supervisor.py','tests/supervisor_worker.py','tests/supervisor_handshake_worker.py','tests/supervisor_timing.py','tests/conftest.py')}
 atomic_json(out/'source.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),sha256=hashes,python=sys.version,platform=platform.platform(),clock_id=d.clock_id,deadline_ns=d.end_ns))
 for i in range(20):
  d.check();folder=out/f'repeat{i:02d}';folder.mkdir();cmd=[sys.executable,'-m','pytest','-q','tests/test_supervisor.py::test_real_worker_lifecycle[before]','--basetemp='+str((folder/'pytest').resolve()),'--junitxml='+str((folder/'tests.xml').resolve())];start=time.monotonic_ns();watchdog=False
  with (folder/'pytest.log').open('wb') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,NEUROMANCER_TEST_ARTIFACTS=str((folder/'retained').resolve()),M008_WORKER_TRACE='1'))
   try:proc.wait(timeout=min(12,d.remaining()))
   except subprocess.TimeoutExpired:
    watchdog=True
    for f in folder.rglob('pid.json'):
     try:os.killpg(json.loads(f.read_text())['pgid'],signal.SIGKILL)
     except ProcessLookupError:pass
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proc.wait(timeout=1)
  rows.append(dict(index=i,returncode=proc.returncode,outer_watchdog=watchdog,outer_elapsed_ns=time.monotonic_ns()-start,command=cmd));atomic_json(out/'results.json',rows)
  if watchdog:raise RuntimeError('Outer watchdog intervention; retain partial evidence')
 atomic_json(out/'complete.json',dict(repeats=len(rows),failed=sum(r['returncode']!=0 for r in rows),remaining_s=d.remaining()))
if __name__=='__main__':main()
