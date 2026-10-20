"""Deterministically rescore committed evidence; no neural acquisition/refitting."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser(); p.add_argument('--raw', type=Path, required=True); p.add_argument('--models', type=Path, required=True)
p.add_argument('--original', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
a = p.parse_args(); began = time.perf_counter(); base = Path(__file__).parent
for script, args in (('analyze.py', ['--raw', str(a.raw), '--models', str(a.models), '--output', str(a.output)]),
                     ('figures.py', ['--analysis', str(a.output), '--raw', str(a.raw), '--models', str(a.models)])):
    subprocess.run([sys.executable, str(base/script), *args], check=True, timeout=900, stdout=subprocess.DEVNULL)
checks = {}
for path in a.output.iterdir():
    old = a.original/path.name
    if path.name == 'comparison.json':
        x = json.loads(path.read_text()); y = json.loads(old.read_text()); x.pop('analysis_wall_s'); y.pop('analysis_wall_s')
        assert x == y; checks[path.name] = 'Identical scientific fields; measured runtime excluded'
    else:
        assert path.read_bytes() == old.read_bytes(), path.name
        checks[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(a.original/'reproducibility.json').write_text(json.dumps(dict(status='PASS', checks=checks, wall_s=time.perf_counter()-began), indent=2)+'\n')
print('Deterministic reanalysis PASS:', len(checks), 'files')
