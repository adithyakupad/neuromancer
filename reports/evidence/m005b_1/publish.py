"""Publish engineering-only decision after all preserved evidence checks."""
import hashlib,json,os,re,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,atomic_json
from neuromancer.clocks import now_ns
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def main():
 d=Deadline.from_environment();d.check();v=read(R/'verification.json');smoke=read(R/'smoke/summary.json');assert v['status']==smoke['status']==read(R/'final_replay.json')['status']=='PASS';assert read(R/'failure_fixtures.json')['status']=='PASS_EXPECTED_FAILURES_RETAINED'
 tests={}
 for name,n in (('tests.xml',169),('final_tests.xml',173)):
  suites=list(ET.parse(R/name).getroot().iter('testsuite'));assert all(int(s.attrib.get('errors',0))+int(s.attrib.get('failures',0))==0 for s in suites);tests[name]=sum(int(s.attrib['tests']) for s in suites);assert tests[name]==n
 assert read(R/'lineage.json')['status']=='PASS'
 for name in ('supervision','fault_supervision','final_supervision','lineage_supervision'):
  t=read(R/name/'terminal.json');assert t['status']=='COMPLETED' and t['cleanup_verified'] and t['deadline_ns']==d.end_ns and t['deadline_clock_id']==d.clock_id
  for w in t['workers']:
   assert w['parent_reaped'] and w['returncode']==0
   try:os.killpg(w['pgid'],0)
   except ProcessLookupError:pass
   else:raise AssertionError('Unreaped worker group')
 hist=read(R/'preservation.json')['historical_sha256']
 for p,h in hist.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 # All old source is unchanged; exact new source used for smoke/final guards is Git-addressable.
 for p,h in smoke['source']['source_hashes'].items():assert hashlib.sha256(subprocess.check_output(['git','show',smoke['source']['head']+':src/'+p])).hexdigest()==h,p
 allocation=sum(p.stat().st_blocks*512 for p in R.rglob('*') if p.is_file() and not p.is_symlink());assert allocation<100*1024**2 and smoke['peak_rss_bytes']<2*1024**3
 text=Path('reports/M005B_1_CONTROLLER_IMPLEMENTATION.md').read_text();assert 'Engineering PASS' in text and 'Scientific acquisition' in text
 decision=dict(engineering='PASS',controller_readiness='PASS_FOR_QUALIFIED_ENGINEERING_CONTRACT',scientific_acquisition='NOT_STARTED_REQUIRES_SEPARATE_AUTHORIZATION_AND_FROZEN_ACQUISITION_PREFLIGHT',scientific_superiority='NOT_TESTED',locked_networks_opened=False,starting_revision='299dbc9dcfe5b5e73204362701afda72dfca6fa1',smoke_revision=smoke['source']['head'],final_controller_revision='90d5037',preregistered_clarification_revision='1d20678',tests=tests,smoke_simulated_seconds=59,networks=[0],noise=[60],independent_verification=v['status'],historical_files_unchanged=len(hist),evidence_allocated_bytes=allocation,deadline_ns=d.end_ns,clock_id=d.clock_id,publication_ns=now_ns(),physical_sleep_test=False,hard_realtime_qualified=False)
 atomic_json(R/'decision.json',decision)
 source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('src/neuromancer/predictive.py'),Path('src/neuromancer/predictive_planner.py'),Path('tests/test_predictive.py')]+list(R.glob('*.py'))};atomic_json(R/'source_manifest.json',source)
 files=[p for p in R.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='manifest.json' and 'publication_supervision' not in p.parts and '__pycache__' not in p.parts];files.extend([Path('reports/M005B_1_CONTROLLER_IMPLEMENTATION.md'),Path('docs/research/011_M005B_CONTROL_PROTOCOL.md'),Path('src/neuromancer/predictive.py'),Path('src/neuromancer/predictive_planner.py'),Path('tests/test_predictive.py')])
 hashes={str(p.relative_to(Path.cwd())) if p.is_absolute() else str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)};atomic_json(R/'manifest.json',dict(sha256=hashes,excluded='self, still-running publication supervisor bookkeeping, Python caches; all numerical evidence included'));d.check();print(json.dumps(decision))
if __name__=='__main__':main()
