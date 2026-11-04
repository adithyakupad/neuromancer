"""Install both review wheels in the reused isolated pinned audit environment."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json
if __name__=='__main__':
 root=Path.cwd();p=root/'reports/performance/evidence';py=sys.executable;d=Deadline.after(300);os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-perf-mpl');os.environ.pop('PYTHONPATH',None)
 wheels=[next(Path('/tmp/neuromancer-v1-release-wheel').glob('*.whl')),next((p/'wheel').glob('*.whl'))];records=[]
 for label,wheel in zip(('release','candidate'),wheels,strict=True):
  out=p/(label+'_wheel_install');commands=[[py,'-m','pip','install','--force-reinstall','--no-deps',str(wheel)],[py,'-m','pip','check'],[py,'-c','import neuromancer,numpy,brian2,scipy,pytest,importlib.metadata; print(neuromancer.__file__); print(importlib.metadata.version("neuromancer"))'],[str(Path(py).parent/'neuromancer-diagnostic'),'--mode','smoke','--output',str(p/(label+'_wheel_smoke'))]]
  old=Path.cwd();os.chdir('/tmp')
  try:r=supervise(commands,out,d,workers=1)
  finally:os.chdir(old)
  assert r['status']=='COMPLETED',r
  with zipfile.ZipFile(wheel) as z:
   src={name:hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist() if name.startswith('neuromancer/') and name.endswith('.py')}
  records.append(dict(label=label,wheel=str(wheel),sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),bytes=wheel.stat().st_size,source_sha256=src,status=r['status']))
 atomic_json(p/'wheel_qualification.json',records)
