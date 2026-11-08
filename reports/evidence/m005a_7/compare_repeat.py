import hashlib,json
from pathlib import Path
r=Path(__file__).resolve().parent;a=r/'analysis';b=r/'repeat_analysis';left={p.name for p in a.iterdir() if p.is_file()};right={p.name for p in b.iterdir() if p.is_file()};assert left==right
for name in left:assert (a/name).read_bytes()==(b/name).read_bytes(),name
(r/'repeat_verification.json').write_text(json.dumps(dict(status='PASS',files=len(left),sha256={name:hashlib.sha256((a/name).read_bytes()).hexdigest() for name in sorted(left)}),indent=2)+'\n')
