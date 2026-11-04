"""One final global budget for tests, benchmarks, replay, plots and wheel build."""
import os,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json
if __name__=='__main__':
 p=Path('reports/performance/evidence');d=Deadline.after(900);os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-perf-mpl');py=sys.executable
 commands=[[py,'-m','pytest','-q','--junitxml='+str(p/'final_tests.xml')],[py,'benchmarks/closed_loop.py','--output',str(p/'workflow_final')],[py,'benchmarks/v1_1.py','--output',str(p/'final')],[py,'scripts/reproduce_v1_evidence.py','--output',str(p/'scientific_reproduction')],[py,'-m','pip','wheel','--no-deps','--no-build-isolation','.','-w',str(p/'wheel')]]
 atomic_json(p/'final_commands.json',commands);r=supervise(commands,p/'final_supervision',d,workers=1);atomic_json(p/'final_status.json',dict(status=r['status'],remaining_s=d.remaining()))
 if r['status']!='COMPLETED':raise RuntimeError(r)
