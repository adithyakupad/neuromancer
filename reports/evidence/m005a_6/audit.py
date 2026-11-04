"""Read-only lineage and history audit, no neural advancement."""
import hashlib,json,subprocess
from pathlib import Path
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;Deadline.from_environment().check()
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=read(r/'preservation.json')['historical_sha256'];assert all(sha(p)==h for p,h in old.items())
m=read('reports/evidence/m005a_5/verification_manifest.json');assert all(sha(p)==h for p,h in m['inventory'].items())
lineage=read('reports/evidence/m005a_5/lineage.json')['trials'];assert len(lineage)==20 and {(x['network'],x['replicate']) for x in lineage}=={(n,k) for n in range(10) for k in (41,42)}
seen=set()
for t in lineage:
 source=Path(t['source']);meta=read(source.parent/'provenance.json');rev=t['source_revision']
 for name,h in t['sha256'].items():assert sha(source/name)==h==sha(Path('reports/evidence/m005a_5/confirmation')/source.name/name)
 if rev not in seen:
  for f,h in meta['source_hashes'].items():assert hashlib.sha256(subprocess.check_output(['git','show',rev+':src/'+f])).hexdigest()==h
  seen.add(rev)
selection=Path('reports/evidence/m005a_3/tuning_analysis/selection.json');assert sha(selection)=='076604e732e1f97d02195c6d3798f0fba1998f4e9605c9492480cf51f794da36'
dec=read('reports/evidence/m005a_5/decision.json');assert dec['scientific']=='FAIL' and dec['stationary']=='PASS' and dec['recovery']=='FAIL' and dec['m005b']=='HOLD'
(r/'lineage_verification.json').write_text(json.dumps(dict(status='PASS',historical_files=len(old),trials=20,branches=160,source_revisions=sorted(seen),selection_sha256=sha(selection),m005a_5_decision=dec,input_inventory_sha256=sha('reports/evidence/m005a_5/verification_manifest.json')),indent=2)+'\n')
Deadline.from_environment().check()
