"""Reanalyze saved M003.1 data without reacquiring neurons or refitting."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main(raw,models,original,output):
    start=time.perf_counter();base=Path(__file__).parent;original=Path(original);output=Path(output);assert not output.exists()
    for script,args in [('analyze.py',[raw,models,str(output)]),('figures.py',[str(output)])]:
        subprocess.run([sys.executable,str(base/script),*args],check=True,stdout=subprocess.DEVNULL)
    checks={}
    for p in sorted(output.iterdir()):
        if p.name=='comparison.json':
            old=json.load(open(original/p.name));new=json.load(open(p));old.pop('analysis_wall_s');new.pop('analysis_wall_s');assert old==new
            checks[p.name]='Identical all scientific fields; measured analysis_wall_s excluded'
        else:
            assert p.read_bytes()==(original/p.name).read_bytes(),p.name
            checks[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    result=dict(status='PASS',checks=checks,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),wall_s=time.perf_counter()-start)
    (original/'reproducibility.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('models');p.add_argument('original');p.add_argument('output');a=p.parse_args();main(a.raw,a.models,a.original,a.output)
