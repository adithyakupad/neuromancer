"""Post-stop read-only report audit; no science imports, tests or trajectories."""
import csv,hashlib,importlib,importlib.metadata,json,math,os,subprocess,sys,types
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
def main():
 # Isolated loading avoids package __init__ -> numpy; it does not repair the environment.
 package=types.ModuleType('_m005b2_stdlib_audit');package.__path__=[str(Path('src/neuromancer').resolve())];sys.modules[package.__name__]=package
 clocks=importlib.import_module(package.__name__+'.clocks');supervisor=importlib.import_module(package.__name__+'.supervisor');clock=clocks.get_clock();samples=[clock.sample() for _ in range(1000)]
 # This is read-only publication, not a restarted scientific/preflight budget.
 begun=clocks.now_ns();limit=supervisor.Deadline.after(60)
 hist=read(R/'preservation.json')['historical_sha256'];old=read('reports/evidence/m005b_1/manifest.json')['sha256']
 for p,h in hist.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 for p,h in old.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 frozen=Path('docs/research/011_M005B_CONTROL_PROTOCOL.md');assert frozen.read_bytes()==subprocess.check_output(['git','show','299dbc9:'+str(frozen)])
 for p in ('src/neuromancer/predictive.py','src/neuromancer/predictive_planner.py','src/neuromancer/control.py','src/neuromancer/_brian.py','src/neuromancer/supervisor.py','src/neuromancer/clocks.py'):
  assert subprocess.check_output(['git','show','901fa5b:'+p])==Path(p).read_bytes()
 env={}
 for p in ('numpy','brian2','pytest','neuromancer'):
  try:env[p]=importlib.metadata.version(p)
  except importlib.metadata.PackageNotFoundError:env[p]=None
 assert all(x is None for x in env.values())
 # Independent scalar proof of every candidate on representative legal priors.
 transitions=0
 for start in (0.,37.3,120.):
  for a in range(0,121,5):
   for b in range(0,121,5):
    q=start
    for tick in range(100):
     target=a if tick<50 else b;lo=max(0.,q-30);hi=min(120.,q+30)
     while q-lo>30:lo=math.nextafter(lo,q)
     while hi-q>30:hi=math.nextafter(hi,q)
     delivered=min(hi,max(lo,target));assert 0<=delivered<=120 and 2*delivered<=240 and abs(delivered-q)<=30;q=delivered;transitions+=1
 s=read('reports/evidence/m005b_1/smoke/summary.json');branch_seconds={k:v['elapsed_s'] for k,v in s['branches'].items()};rates={k:v/2 for k,v in branch_seconds.items()};batch=read('reports/evidence/m005a_7/acquisition_closure.json')['elapsed_s']/7420
 manifest=read(R/'prospective_manifest.json');dev=sum(x['stage']=='DEVELOPMENT' for x in manifest['cohorts']);val=sum(x['stage']=='VALIDATION' for x in manifest['cohorts']);fault=sum(x['stage']=='SECONDARY_FAULT' for x in manifest['cohorts']);assert (dev,val,fault)==(20,10,3)
 def primary(jobs,rls):return jobs*2*64*(rates['FIXED']+rls+rates['BIAS'])/3+jobs*(51+7*64)*batch
 def faults(rls):return fault*4*64*(rls+min(rates.values()))/3+fault*51*batch
 development=primary(dev,rates['RLS'])+faults(rates['RLS']);validation=primary(val,rates['RLS'])
 projection=dict(measured_branch_s=branch_seconds,per_simulated_second_s=rates,batched_aggregate_wall_s_per_sim_s=batch,development_primary_s=primary(dev,rates['RLS']),development_secondary_fault_s=faults(rates['RLS']),development_combined_s=development,development_cap_s=10800,development_excess_s=development-10800,development_excess_fraction=development/10800-1,validation_s=validation,validation_cap_s=5400,faster_replay_sensitivity_development_s=primary(dev,rates['RLS_REPLAY'])+faults(rates['RLS_REPLAY']),ideal_parallel_workers=3,forecast_not_benchmark=True,secondary_PI_proxy='fastest archived per-tick branch; optimistic unmeasured PI proxy',new_scientific_trajectories=0)
 assert development>10800
 (R/'resource_projection.json').write_text(json.dumps(projection,indent=2)+'\n')
 with (R/'resource_projection.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['stage','forecast_s','cap_s','status']);w.writerow(['DEVELOPMENT_INCLUDING_FAULTS',development,10800,'HOLD']);w.writerow(['VALIDATION_CONDITIONAL',validation,5400,'CLOSED_BY_READINESS'])
 result=dict(status='HOLD',blockers=['FROZEN_DEVELOPMENT_RESOURCE_PROJECTION_EXCEEDS_CAP','NUMPY_BRIAN2_PYTEST_NOT_AVAILABLE_IN_PRIOR_TEMP_ENVIRONMENT'],historical_files_unchanged=len(hist),prior_artifacts_checked=len(old),prior_engineering_evidence=read('reports/evidence/m005b_1/decision.json')['engineering'],native_clock_samples=len(samples),clock_id=clocks.clock_domain(),supervisor_source_loaded=True,science_package_importable=False,environment=dict(executable=sys.executable,prefix=sys.prefix,versions=env),independent_scalar_candidates=625,prior_currents=[0,37.3,120],admissible_transitions=transitions,actual_numpy_planner_executed=False,fresh_regression_tests='NOT_RUN_IMPORT_FAILURE',scientific_trajectories=0,validation_opened=False,locked_opened=False,scientific_gates_evaluated=False,read_only_audit_elapsed_s=(clocks.now_ns()-begun)/1e9)
 (R/'readiness.json').write_text(json.dumps(result,indent=2)+'\n');limit.check();print(json.dumps(result))
if __name__=='__main__':main()
