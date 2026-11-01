from pathlib import Path
import os,sys
from neuromancer.supervisor import Deadline,supervise
R=Path('reports/evidence/m007');d=Deadline.after(600);os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,VECLIB_MAXIMUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-m007-mpl');result=supervise([[sys.executable,'-m','pytest','-q','--basetemp='+str(R/'provenance_repair_fixtures'),'--junitxml='+str(R/'repaired_tests.xml')]],R/'provenance_repair_supervision',d,workers=1)
if result['status']!='COMPLETED':raise RuntimeError('Provenance repair not qualified')
