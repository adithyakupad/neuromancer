"""M007 audit-only verification, fresh1800s budget; no scientific acquisition."""
import importlib,json,os,pkgutil,sys
from pathlib import Path
import neuromancer,numpy,brian2,scipy,pytest
from neuromancer.supervisor import Deadline,supervise,atomic_json
R=Path('reports/evidence/m007');P=sys.executable;d=Deadline.after(1800)
os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,VECLIB_MAXIMUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-m007-mpl')
assert 'site-packages' in neuromancer.__file__ and '/tmp/neuromancer-m007' in neuromancer.__file__;mods=[]
for m in pkgutil.iter_modules(neuromancer.__path__):importlib.import_module('neuromancer.'+m.name);mods.append(m.name)
atomic_json(R/'environment.json',dict(python=sys.version,package=neuromancer.__file__,versions=dict(numpy=numpy.__version__,brian2=brian2.__version__,scipy=scipy.__version__,pytest=pytest.__version__),imports=mods,deadline_ns=d.end_ns,clock=d.clock_id))
commands=[[P,'-m','pytest','-q','--basetemp='+str(R/'regression_fixtures'),'--junitxml='+str(R/'tests.xml')],[str(Path(P).parent/'neuromancer-diagnostic'),'--mode','smoke','--output',str(R/'smoke')],[P,str(R/'reproduce.py')],[P,'reports/evidence/v1_finish/verify_study.py','reports/evidence/v1_finish/m005b/primary',str(R/'model_replay_primary.json')],[P,'reports/evidence/v1_finish/verify_study.py','reports/evidence/v1_finish/m005b/faults',str(R/'model_replay_faults.json')],[P,'-m','neuromancer.m005b_analysis','reports/evidence/v1_finish/m005b/primary',str(R/'analysis_reproduction')],[P,'reports/evidence/v1_finish/research_figures.py','reports/evidence/v1_finish/m005b/primary',str(R/'analysis_reproduction'),str(R/'figure_reproduction')]]
atomic_json(R/'commands.json',commands);result=supervise(commands,R/'supervision',d,workers=1)
if result['status']!='COMPLETED':raise RuntimeError('Audit verification failed; retain failure logs')
atomic_json(R/'local_qualification.json',dict(status='PASS',commands=len(commands),remaining_s=d.remaining()))
