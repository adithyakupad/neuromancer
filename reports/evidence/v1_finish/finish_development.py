"""Prospective post-acquisition sequence. No controller change or selection."""
import json,os,subprocess,sys,time,hashlib
from pathlib import Path
from neuromancer.clocks import now_ns
from neuromancer.supervisor import Deadline,supervise,atomic_json
B=Path('reports/evidence/v1_finish/m005b');PY=sys.executable

def main():
 launch=json.loads((B/'primary_launch.json').read_text());acq=Deadline(**launch['deadline'])
 # Wait only for completion/failure markers; never inspect scientific outcomes.
 while not (B/'primary_closure.json').exists():
  acq.check();time.sleep(min(10.,acq.remaining()))
 closure=json.loads((B/'primary_closure.json').read_text())
 if closure['status']!='COMPLETE':raise RuntimeError('Primary acquisition incomplete; no analysis completion claim')
 d=Deadline.after(2400);env=dict(os.environ,NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id);os.environ.update({k:env[k] for k in ('NEUROMANCER_DEADLINE_NS','NEUROMANCER_DEADLINE_CLOCK')});atomic_json(B/'analysis_launch.json',dict(start_ns=now_ns(),deadline=dict(end_ns=d.end_ns,clock_id=d.clock_id),primary_source=launch['source_revision']))
 commands=[
  [PY,'reports/evidence/v1_finish/verify_study.py',str(B/'primary'),str(B/'primary_verification.json')],
  [PY,'-m','neuromancer.m005b_analysis',str(B/'primary'),str(B/'analysis_primary')],
  [PY,'reports/evidence/v1_finish/verify_metrics.py',str(B/'primary'),str(B/'analysis_primary'),str(B/'primary_metrics_verification.json')]]
 result=supervise(commands,B/'analysis_primary_supervision',d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError('Independent primary analysis incomplete')
 verified=json.loads((B/'primary_verification.json').read_text());summary=json.loads((B/'analysis_primary/summary.json').read_text());atomic_json(B/'frozen_development_decision.json',dict(frozen_ns=now_ns(),source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),summary_sha256=hashlib.sha256((B/'analysis_primary/summary.json').read_bytes()).hexdigest(),primary_source=launch['source_revision'],scientific_pass=summary['scientific_pass'],valid=verified['primary_instrument_valid'] and summary['execution_numerically_valid'],selection='none; protocol parameters frozen'))
 if not verified['primary_instrument_valid'] or not summary['execution_numerically_valid']:raise RuntimeError('Mandatory primary instrument gate failed; stop')
 acq.check()
 command=[PY,'-m','neuromancer.m005b_study','acquire','--phase','faults','--output',str(B/'faults'),'--prior',str(B/'primary_launch.json')]
 atomic_json(B/'fault_command.json',dict(command=command,original_deadline=launch['deadline']));result=subprocess.run(command,env=env)
 if result.returncode:raise RuntimeError('Secondary fault acquisition incomplete')
 commands=[
  [PY,'reports/evidence/v1_finish/verify_study.py',str(B/'faults'),str(B/'fault_verification.json')],
  [PY,'-m','neuromancer.m005b_analysis',str(B/'faults'),str(B/'analysis_faults')],
  [PY,'reports/evidence/v1_finish/shadow_controls.py',str(B/'primary'),str(B/'shadows')],
  [PY,'reports/evidence/v1_finish/research_figures.py',str(B/'primary'),str(B/'analysis_primary'),str(B/'figures_primary')]]
 result=supervise(commands,B/'analysis_secondary_supervision',d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError('Secondary analysis incomplete')
 d.check();atomic_json(B/'development_finished.json',dict(status='COMPLETE',scientific_pass=summary['scientific_pass'],validation_permitted=summary['scientific_pass'],locked_networks_opened=False,finished_ns=now_ns(),analysis_deadline_ns=d.end_ns))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  atomic_json(B/'post_acquisition_failure.json',dict(status='PARTIAL',error=repr(exc)));raise
