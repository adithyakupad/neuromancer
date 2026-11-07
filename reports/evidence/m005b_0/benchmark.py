"""Bounded synthetic planner measurements and historical input-design-only audit."""
import hashlib,json,platform,resource,sys,time
from pathlib import Path
import numpy as np
from prototype import plan
from test_design import fixture
from neuromancer.clocks import now_ns,clock_domain
from neuromancer.supervisor import Deadline
R=Path(__file__).resolve().parent

def main():
 d=Deadline.from_environment();d.check();began=now_ns();u,y,(r,z,v,p)=fixture();rows=[]
 for i in range(100):
  d.check();q=float((i*17)%121);history=np.zeros((9,4));history[:,::2]=q
  start=now_ns()
  try:
   result=plan(r,r['coef'],history,10.+(i%3)*.1,51_000_000);status='complete';chosen=result['chosen'];internal=result['elapsed_ns'];assert internal<=250_000_000
  except TimeoutError as e:status=str(e);chosen=None;internal=None
  rows.append(dict(index=i,status=status,elapsed_ns=now_ns()-start,internal_ns=internal,chosen=chosen))
 # Read only historical CALIBRATION inputs, never new neural outcomes.
 f=Path('reports/evidence/m005a_7/trials/n0_r45/prefix.npz');old=dict(np.load(f));k=np.arange(800,2350);q=old['delivered'][:,0]
 reduced=np.c_[np.ones(len(k)),*[q[k-j] for j in range(10)]];reduced[:,1:]=(reduced[:,1:]-reduced[:,1:].mean(0))/np.maximum(reduced[:,1:].std(0),1)
 rank=int(np.linalg.matrix_rank(reduced));condition=float(np.linalg.cond(reduced));lat=np.array([row['elapsed_ns']/1e6 for row in rows]);p95=float(np.quantile(lat,.95));overhead_dev=8448*p95/1000;overhead_val=3840*p95/1000
 result=dict(status='PASS' if all(x['status']=='complete' for x in rows) and max(lat)<=250 else 'HOLD',kind='synthetic_only_no_neural_acquisition',candidates_per_plan=625,horizon_bins=100,decisions=rows,latency_ms=dict(min=float(lat.min()),median=float(np.median(lat)),p95=p95,max=float(lat.max())),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,clock_id=clock_domain(),wall_s=(now_ns()-began)/1e9,historical_input_only_audit=dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),rows=[800,2350],reduced_rank=rank,reduced_condition=condition),future_estimate_s=dict(development_neural=19349*2187.636798083/7420,validation_neural=8830*2187.636798083/7420,development_serial_planning=overhead_dev,validation_serial_planning=overhead_val),environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,blas_threads='requested1_actual_unverified'))
 (R/'benchmark.json').write_text(json.dumps(result,indent=2)+'\n');d.check();print(json.dumps({k:v for k,v in result.items() if k!='decisions'}));assert result['status']=='PASS'
if __name__=='__main__':main()
