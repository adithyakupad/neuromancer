"""Run a bounded test/verification command using the qualified supervisor."""
import os,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise
if __name__=='__main__':
 output=Path(sys.argv[1]);d=Deadline.after(900);os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-perf-mpl')
 result=supervise([sys.argv[2:]],output,d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError(result)
