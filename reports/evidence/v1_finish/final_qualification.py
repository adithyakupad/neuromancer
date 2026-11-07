"""Finish V1 verification inside the original cohort analysis deadline."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise,atomic_json
B=Path('reports/evidence/v1_finish/m005b');R=B.parent;PY=sys.executable

def main():
 assert json.loads((B/'development_finished.json').read_text())['status']=='COMPLETE'
 launch=json.loads((B/'analysis_launch.json').read_text());d=Deadline(**launch['deadline']);d.check();os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id);fixtures=R/'closing_regression_fixtures';assert not fixtures.exists(),'Preserve previous test fixtures'
 commands=[
  [PY,str(R/'prediction_summary.py'),str(B/'analysis_primary'),str(B/'prediction_summary.json')],
  [PY,str(R/'supplemental_metrics.py'),str(B/'primary'),str(B/'supplement_primary')],
  [PY,str(R/'supplemental_metrics.py'),str(B/'faults'),str(B/'supplement_faults')],
  [PY,'-m','pytest','-q','--basetemp='+str(fixtures),'--junitxml='+str(B/'final_tests.xml')],
  [PY,str(R/'final_integrity.py')],
  [PY,str(R/'build_research_report.py')]]
 atomic_json(B/'final_qualification_launch.json',dict(deadline=launch['deadline'],source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),commands=commands,auxiliary_source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in R.glob('*.py')}))
 result=supervise(commands,B/'final_qualification_supervision',d,workers=1)
 if result['status']!='COMPLETED':raise RuntimeError('Final qualification incomplete')
 d.check();atomic_json(B/'final_qualification_complete.json',dict(status='PASS',analysis_deadline=launch['deadline'],full_regression_xml=str(B/'final_tests.xml'),independent_integrity=str(B/'final_integrity.json')))
if __name__=='__main__':main()
