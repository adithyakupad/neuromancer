"""Retain synthetic fixture/model and verify design, lineage, resources and closure."""
import hashlib,json,os,platform,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from prototype import plan
from test_design import fixture
from neuromancer.supervisor import Deadline
from neuromancer.clocks import now_ns
R=Path(__file__).resolve().parent;BASE=Path.cwd()

def read(p):return json.loads(p.read_text())
def main():
 d=Deadline.from_environment();d.check()
 b=read(R/'benchmark.json');v=read(R/'independent_verification.json');res=read(R/'regression_resource.json');assert b['status']==v['status']==res['status']=='PASS'
 counts={}
 for f,n in (('synthetic_tests.xml',8),('regression_tests.xml',157),('measured_regression_tests.xml',157)):
  suites=list(ET.parse(R/f).getroot().iter('testsuite'));assert all(int(x.attrib.get('errors',0))+int(x.attrib.get('failures',0))==0 for x in suites);counts[f]=sum(int(x.attrib['tests']) for x in suites);assert counts[f]==n
 for name in ('supervision','independent_supervision'):
  t=read(R/name/'terminal.json');assert t['status']=='COMPLETED' and t['cleanup_verified'] and t['deadline_ns']==d.end_ns and t['deadline_clock_id']==d.clock_id
  for w in t['workers']:
   assert w['parent_reaped'] and w['returncode']==0
   try:os.killpg(w['pgid'],0)
   except ProcessLookupError:pass
   else:raise AssertionError('Unreaped process group')
 hist=read(R/'preservation.json')['historical_sha256']
 for p,h in hist.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 proto=Path('docs/research/011_M005B_CONTROL_PROTOCOL.md');assert proto.read_bytes()==subprocess.check_output(['git','show','f13b137:'+str(proto)])
 u,y,(record,z,target,p)=fixture();result=plan(record,record['coef'],u[-9:],10.,51_000_000,limit_s=10)
 np.savez_compressed(R/'canonical_synthetic.npz',inputs=u,outputs=y,features=z,centered_targets=target,initial_information_inverse=p,coefficients=record['coef'],history=u[-9:],plans=result['bank'],predictions=result['predictions'],cost=result['cost'],selected=result['chosen'])
 (R/'synthetic_model.json').write_text(json.dumps(record,indent=2)+'\n')
 allocation=sum(p.stat().st_blocks*512 for p in R.rglob('*') if p.is_file() and not p.is_symlink());assert allocation<50*1024**2
 result=dict(design='PASS',scientific='NOT_RUN',acquisition='HOLD_PENDING_SEPARATE_AUTHORIZATION_AND_IMPLEMENTATION_GATE',historical_m005a5='FAIL_UNCHANGED',m005a7='PASS_UNCHANGED',new_scientific_trajectories=0,locked_networks_opened=False,tests=counts,clock_id=d.clock_id,deadline_ns=d.end_ns,checked_ns=now_ns(),elapsed_since_check_start_s=(now_ns()-read(R/'closure.json')['started_ns'])/1e9,new_evidence_allocated_bytes=allocation,evidence_cap_bytes=50*1024**2,historical_files_unchanged=len(hist),preregistration_revision='f13b13786ad1a17a76f2cf9c6ac6412df51b2191',python=sys.version,platform=platform.platform())
 (R/'decision.json').write_text(json.dumps(result,indent=2)+'\n')
 files=[p for p in R.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='manifest.json' and 'publication_supervision' not in p.parts and '__pycache__' not in p.parts]
 files.extend([Path('reports/M005B_0_CONTROL_DESIGN.md'),proto]);manifest={str(p.relative_to(BASE)) if p.is_absolute() else str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
 (R/'manifest.json').write_text(json.dumps(dict(sha256=manifest,excluded='self, publication supervisor bookkeeping and Python caches; no numerical evidence excluded'),indent=2)+'\n');d.check();print(json.dumps(result))
if __name__=='__main__':main()
