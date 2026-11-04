"""Distinguish intentionally optimized source from immutable scientific evidence."""
import hashlib,json
from pathlib import Path
p=Path('reports/performance/evidence');old=json.loads((p/'historical_manifest.json').read_text());changed={};missing=[]
for name,digest in old.items():
 f=Path(name)
 if not f.exists():missing.append(name);continue
 new=hashlib.sha256(f.read_bytes()).hexdigest()
 if new!=digest:changed[name]=dict(before=digest,after=new)
allowed={'src/neuromancer/_brian.py','src/neuromancer/predictive_planner.py','tests/test_calibration.py','pyproject.toml'}
assert not missing and set(changed)==allowed,(missing,changed)
for name,snapshot in [('src/neuromancer/_brian.py','docs/history/BRIAN_V1_SNAPSHOT.py'),('src/neuromancer/predictive_planner.py','docs/history/PLANNER_V1_SNAPSHOT.py')]:assert hashlib.sha256(Path(snapshot).read_bytes()).hexdigest()==old[name]
out=dict(status='PASS',baseline_files=len(old),unchanged=len(old)-len(changed),missing=missing,authorized_performance_differences=changed,scientific_protocol_and_numerical_evidence='unchanged')
(p/'preservation_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
