"""Resume only unfinished analysis/fault stages; retain both original deadlines."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from neuromancer.clocks import now_ns
from neuromancer.supervisor import Deadline,supervise,atomic_json
B=Path('reports/evidence/v1_finish/m005b');R=B.parent;PY=sys.executable

def main():
 d=Deadline(**json.loads((B/'analysis_launch.json').read_text())['deadline']);d.check();os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id)
 commands=[[PY,'-m','pytest','-q','tests/test_m005b_complete_analysis.py','--basetemp='+str(R/'path_repair_fixtures'),'--junitxml='+str(B/'path_repair_tests.xml')],[PY,str(R/'verify_metrics.py'),str(B/'primary'),str(B/'analysis_primary'),str(B/'primary_metrics_verification.json')]]
 result=supervise(commands,B/'analysis_publication_recovery_supervision',d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError('Publication repair qualification failed')
 verified=json.loads((B/'primary_verification.json').read_text());s=json.loads((B/'analysis_primary/summary.json').read_text());assert verified['primary_instrument_valid'] and s['execution_numerically_valid']
 atomic_json(B/'frozen_development_decision.json',dict(frozen_ns=now_ns(),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),summary_sha256=hashlib.sha256((B/'analysis_primary/summary.json').read_bytes()).hexdigest(),primary_source=json.loads((B/'primary_launch.json').read_text())['source_revision'],scientific_pass=s['scientific_pass'],valid=True,selection='none; all protocol settings unchanged',publication_repair='Output Path conversion only; original failure retained'))
 acq=Deadline(**json.loads((B/'primary_launch.json').read_text())['deadline']);acq.check();assert not (B/'faults').exists()
 command=[PY,'-m','neuromancer.m005b_study','acquire','--phase','faults','--output',str(B/'faults'),'--prior',str(B/'primary_launch.json')];atomic_json(B/'fault_command.json',dict(command=command,original_deadline=json.loads((B/'primary_launch.json').read_text())['deadline']));result=subprocess.run(command)
 if result.returncode:raise RuntimeError('Secondary faults incomplete')
 commands=[[PY,str(R/'verify_study.py'),str(B/'faults'),str(B/'fault_verification.json')],[PY,'-m','neuromancer.m005b_analysis',str(B/'faults'),str(B/'analysis_faults')],[PY,str(R/'shadow_controls.py'),str(B/'primary'),str(B/'shadows')],[PY,str(R/'research_figures.py'),str(B/'primary'),str(B/'analysis_primary'),str(B/'figures_primary')]]
 result=supervise(commands,B/'analysis_secondary_supervision',d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError('Secondary analysis incomplete')
 d.check();atomic_json(B/'development_finished.json',dict(status='COMPLETE',scientific_pass=s['scientific_pass'],validation_permitted=s['scientific_pass'],locked_networks_opened=False,finished_ns=now_ns(),analysis_deadline_ns=d.end_ns,publication_recovery=True))
if __name__=='__main__':
 try:main()
 except BaseException as exc:atomic_json(B/'publication_recovery_failure.json',dict(status='PARTIAL',error=repr(exc)));raise
