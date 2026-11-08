"""Verify V1 scientific source/evidence and the explicit reliability-only backport."""
import hashlib,json,os,subprocess
from pathlib import Path
base='c7012fc4d002a9904abbb68a21a554e11e78d570';allowed={'.github/workflows/ci.yml','.github/workflows/v1-qualification.yml','src/neuromancer/supervisor.py','tests/supervisor_worker.py','tests/test_supervisor.py','tests/test_calibration.py'};changed={};count=0
for record in subprocess.check_output(['git','ls-tree','-rz',base]).split(b'\0'):
 if not record:continue
 meta,name=record.split(b'\t',1);name=name.decode();p=Path(name);assert p.exists() or p.is_symlink(),name
 data=os.readlink(p).encode() if p.is_symlink() else p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();count+=1
 if actual!=meta.split()[2].decode():changed[name]=hashlib.sha256(data).hexdigest()
assert set(changed)==allowed,changed
m=json.loads(Path('reports/engineering/evidence/m009/backport_manifest.json').read_text())
for n,h in m['exact_copies'].items():
 if n=='.github/workflows/v1-qualification.yml':
  original=subprocess.check_output(['git','show','4e180c35:'+n])
  assert hashlib.sha256(original).hexdigest()==h
  assert Path(n).read_bytes()==original.replace(b'macos-latest',b'macos-15-intel')
 else:assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
result=dict(status='PASS',base=base,starting_files=count,unchanged=count-len(changed),engineering_changes=changed,all_numeric_source_and_scientific_evidence='unchanged',m008_exact_copies_except_declared_runner_label=True,runner_clarification='CI_RUNNER_CLARIFICATION.md')
Path('reports/engineering/evidence/m009/preservation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
