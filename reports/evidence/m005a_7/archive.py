"""Final read-only lineage/resource reconciliation and complete stable-file inventory."""
import hashlib,json,os
from pathlib import Path
from neuromancer.supervisor import Deadline
from neuromancer.clocks import now_ns
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def allocation(root):return sum(f.stat().st_blocks*512 for f in root.rglob('*') if f.is_file() and not f.is_symlink())
def main():
 d=Deadline.from_environment();d.check()
 for p,h in read(R/'preservation.json')['historical_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
 for name in ('preflight_supervision','verification_supervision','publication_supervision'):
  t=read(R/name/'terminal.json');assert t['status']=='COMPLETED' and t['cleanup_verified']
  for w in t['workers']:
   assert w['parent_reaped']
   try:os.killpg(w['pgid'],0)
   except ProcessLookupError:pass
   else:raise AssertionError('Surviving worker group')
 new=allocation(R);total=sum(allocation(x) for x in list(Path('reports/evidence').glob('m005a*'))+list(Path('runs').glob('m005a-*')))
 assert new<150*1024**2 and total<500*1024**2
 out=dict(status='PASS',new_evidence_allocated_bytes=new,all_m005a_allocated_bytes=total,new_cap_bytes=150*1024**2,all_cap_bytes=500*1024**2,deadline_ns=d.end_ns,clock_id=d.clock_id,checked_ns=now_ns(),historical_files=len(read(R/'preservation.json')['historical_sha256']),physical_suspend_test=False,monitor_cadence_deviation='Recorded 5.158145–5.965510s; nominal <=5s not achieved, caps/deadline unaltered')
 (R/'final_resource_verification.json').write_text(json.dumps(out,indent=2)+'\n')
 files=[p for p in R.rglob('*') if p.is_file() and not p.is_symlink() and p.name!='artifact_manifest.json' and not any(x.startswith('publication_') and x.endswith('_supervision') for x in p.parts)]
 files += [Path('reports/M005A_7_EXTENDED_RECOVERY.md'),Path('docs/research/010_M005A_7_EXTENDED_RECOVERY_PROTOCOL.md'),Path('src/neuromancer/extended_recovery.py'),Path('src/neuromancer/recovery_metrics.py'),Path('tests/test_extended_recovery.py')]
 manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
 (R/'artifact_manifest.json').write_text(json.dumps(dict(status='PASS',sha256=manifest,excluded='This manifest and publication supervisor bookkeeping; no neural data excluded'),indent=2)+'\n');d.check()
 print(json.dumps(out))
if __name__=='__main__':main()
