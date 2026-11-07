"""Recompute frozen M003 analysis/figures byte-for-byte without neural acquisition."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main(raw,models,original,output,stationary=None):
    began=time.perf_counter();base=Path(__file__).parent;original=Path(original);output=Path(output)
    assert not output.exists(),'Never overwrite an analysis'
    extra=['--stationary',stationary] if stationary else []
    for script,args in [('analyze.py',[raw,models,str(output),*extra]),('figures.py',[str(output),*extra]),('summarize.py',[str(output)])]:
        subprocess.run([sys.executable,str(base/script),*args],check=True,stdout=subprocess.DEVNULL)
    checked={}
    for file in sorted(output.iterdir()):
        if file.name=='analysis_lineage.json':continue
        assert file.is_file() and (original/file.name).read_bytes()==file.read_bytes(),file.name
        checked[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
    old=json.loads((original/'analysis_lineage.json').read_text());new=json.loads((output/'analysis_lineage.json').read_text())
    assert {k:v for k,v in old.items() if k!='wall_ns'}=={k:v for k,v in new.items() if k!='wall_ns'}
    result=dict(status='PASS',files_sha256=checked,wall_s=time.perf_counter()-began,
        excluded='Only measured analysis_lineage.wall_ns differs; all numerical outputs, model selection, data archives and PNG/SVG files agree byte-for-byte.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (original/'reproducibility.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('models');p.add_argument('original');p.add_argument('output');p.add_argument('--stationary');a=p.parse_args();main(a.raw,a.models,a.original,a.output,a.stationary)
