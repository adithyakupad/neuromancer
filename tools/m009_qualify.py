"""Bounded V1 backport qualification; no scientific acquisition."""
import json,os,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json
if __name__=='__main__':
 p=Path('reports/engineering/evidence/m009');d=Deadline.after(900);py=sys.executable
 os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,NEUROMANCER_TEST_ARTIFACTS=str(p/'test_artifacts'),M008_WORKER_TRACE='1',VECLIB_MAXIMUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-m009-mpl')
 commands=[[py,'-m','pip','check'],[py,'-m','pytest','-q','--basetemp='+str(p/'test_tmp'),'--junitxml='+str(p/'tests.xml')],[py,'tools/m008_traced_repeats.py',str(p/'process_trials')],[py,'-m','pip','wheel','--no-deps','--no-build-isolation','.','-w',str(p/'wheel')]]
 atomic_json(p/'commands.json',commands);r=supervise(commands,p/'qualification',d,workers=1)
 atomic_json(p/'qualification_status.json',dict(status=r['status'],remaining_s=d.remaining()))
 if r['status']!='COMPLETED':raise RuntimeError(r)
