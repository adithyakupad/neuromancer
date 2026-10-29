"""Freeze unchanged scientific specification after execution qualification."""
import importlib,json,pkgutil,sys,hashlib,os
from pathlib import Path
import neuromancer
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent
def main():
 d=Deadline.from_environment() if 'NEUROMANCER_DEADLINE_NS' in os.environ else Deadline(**json.loads((R/'freeze_deadline.json').read_text()));d.check()
 for p in ('resource_readiness.json','runner_verification.json','codec_qualification.json'):
  assert json.loads((R/p).read_text())['status']=='PASS'
 for p in ('profile/qualification.json','profile_extended/qualification.json'):
  assert json.loads((R/p).read_text())['status']=='PASS'
 modules=[m.name for m in pkgutil.iter_modules(neuromancer.__path__,neuromancer.__name__+'.')]
 for name in modules:importlib.import_module(name)
 import numpy,brian2,scipy,pytest
 assert (numpy.__version__,brian2.__version__,scipy.__version__,pytest.__version__)==('2.5.4','2.10.1','1.18.0','9.1.1')
 from neuromancer.m005b_study import jobs,BANK
 protocol=Path('docs/research/011_M005B_CONTROL_PROTOCOL.md')
 for p,h in json.loads((R/'preservation.json').read_text())['historical_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
 record=dict(status='PASS',all_project_modules_imported=modules,protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),controller_source_unchanged=True,primary_jobs=jobs('primary'),validation_jobs=jobs('validation'),fault_jobs=jobs('faults'),branch_bank=BANK,control_s=64,prefix_s=51,gain_change_s=16,model=dict(q=10,regularization=.1,rho=.999),PI=dict(kp=10,ki=5),horizon_s=2,candidates=625,workers=3,budgets=dict(development_s=10800,validation_s=5400,analysis_s=2400),scientific_gates_unchanged=True,no_selection_permitted=True,scientific_outcomes_opened=False)
 atomic_json(R/'acquisition_freeze.json',record);d.check();print('PASS: environment, imports, preserved evidence and scientific freeze')
if __name__=='__main__':main()
