"""Exact deterministic postprocessing check, excluding summary's runtime only."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('first',type=Path);p.add_argument('second',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
left={f.name for f in a.first.iterdir() if f.is_file()};right={f.name for f in a.second.iterdir() if f.is_file()}
assert left==right
hashes={}
for name in sorted(left):
    x=(a.first/name).read_bytes();y=(a.second/name).read_bytes()
    if name=='summary.json':
        x=json.loads(x);y=json.loads(y);x.pop('wall_s');y.pop('wall_s');assert x==y
    else:assert x==y,name
    hashes[name]=hashlib.sha256((a.first/name).read_bytes()).hexdigest()
a.output.write_text(json.dumps(dict(status='PASS',files=len(left),runtime_field_excluded='summary.wall_s',first_sha256=hashes),indent=2)+'\n')
