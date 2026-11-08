"""Read-only numerical/source/clock and independent action-bank readiness audit."""
import csv,hashlib,json,os,subprocess,sys
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json
from neuromancer.clocks import get_clock,clock_domain
from neuromancer.predictive_planner import bank
from neuromancer.control import project
R=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
def main():
 d=Deadline.from_environment();d.check();hist=read(R/'preservation.json')['historical_sha256']
 for p,h in hist.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 old=read('reports/evidence/m005b_1/manifest.json')['sha256']
 for p,h in old.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 assert subprocess.check_output(['git','show','299dbc9dcfe5b5e73204362701afda72dfca6fa1:docs/research/011_M005B_CONTROL_PROTOCOL.md'])==Path('docs/research/011_M005B_CONTROL_PROTOCOL.md').read_bytes()
 for p in ('src/neuromancer/predictive.py','src/neuromancer/predictive_planner.py','src/neuromancer/control.py','src/neuromancer/_brian.py','src/neuromancer/supervisor.py','src/neuromancer/clocks.py'):
  assert subprocess.check_output(['git','show','901fa5b:'+p])==Path(p).read_bytes()
 decision=read('reports/evidence/m005b_1/decision.json');assert decision['engineering']=='PASS';assert read('reports/evidence/m005b_1/final_replay.json')['status']=='PASS'
 clock=[get_clock().sample() for _ in range(1000)];assert len({x['clock_id'] for x in clock})==1 and clock[0]['clock_id']==clock_domain()
 for prior in (0.,37.3,120.):
  q0,q1,q=bank(prior)
  for i in range(625):
   p=np.array([prior,0.,prior,0.])
   for tick in range(100):
    request=np.array([q0[i] if tick<50 else q1[i],0.,q0[i] if tick<50 else q1[i],0.]);p,_=project(request,p)
    np.testing.assert_array_equal(p,[q[i,tick],0,q[i,tick],0])
  assert (q>=0).all() and (q<=120).all() and (abs(np.diff(np.c_[np.full(625,prior),q],axis=1))<=30).all()
 # Role-weighted resource projection independently sourced from archived measurements.
 s=read('reports/evidence/m005b_1/smoke/summary.json');seconds={k:x['elapsed_s'] for k,x in s['branches'].items()};rates={k:v/2 for k,v in seconds.items()};batch=2187.636798083/7420
 primary_predictive=2560*sum(rates[k] for k in ('FIXED','RLS','BIAS'))/3
 primary_other=(17660-7680)*batch
 faults=768*(rates['RLS']+min(rates.values()))/3+153*batch
 development=primary_predictive+primary_other+faults
 validation=1280*sum(rates[k] for k in ('FIXED','RLS','BIAS'))/3+(8830-3840)*batch
 faster_primary=2560*(rates['FIXED']+rates['RLS_REPLAY']+rates['BIAS'])/3+primary_other
 faster_faults=768*(rates['RLS_REPLAY']+min(rates.values()))/3+153*batch
 projection=dict(measured_branch_s=seconds,per_simulated_second_s=rates,batched_aggregate_wall_s_per_sim_s=batch,development_primary_s=primary_predictive+primary_other,development_secondary_fault_s=faults,development_combined_s=development,development_cap_s=10800,development_excess_s=development-10800,validation_s=validation,validation_cap_s=5400,readiness='HOLD' if development>10800 or validation>5400 else 'PASS',faster_replay_sensitivity_development_s=faster_primary+faster_faults,ideal_parallel_workers=3,forecast_not_benchmark=True,secondary_PI_proxy='fastest archived per-tick branch; unmeasured proxy, optimistic',additional_current_study_trajectories=0)
 assert projection['readiness']=='HOLD'
 atomic_json(R/'resource_projection.json',projection)
 with (R/'resource_projection.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['stage','forecast_s','cap_s','status']);w.writerow(['DEVELOPMENT_INCLUDING_FAULTS',development,10800,'HOLD']);w.writerow(['VALIDATION_CONDITIONAL',validation,5400,'NOT_OPENED'])
 atomic_json(R/'readiness.json',dict(status='HOLD',reason='FROZEN_DEVELOPMENT_RESOURCE_FEASIBILITY_GATE',engineering_evidence='PASS_PRESERVED',historical_files_unchanged=len(hist),prior_artifacts_checked=len(old),independent_candidates=625,prior_currents_tested=[0,37.3,120],exact_projector_transitions=187500,clock_samples=len(clock),clock_id=clock_domain(),protocol_unchanged=True,controllers_unchanged=True,scientific_trajectories=0,validation_opened=False,locked_opened=False))
 d.check();print(json.dumps(projection))
if __name__=='__main__':main()
