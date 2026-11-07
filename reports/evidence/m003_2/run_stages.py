"""Bounded sequential post-acquisition stages, with exclusive output directories."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

base = Path(__file__).parent
raw = Path('runs/m003-2-01'); models = Path('runs/m003-2-models-01'); analysis = Path('runs/m003-2-analysis-01')
start = time.monotonic()
while not (raw/'summary.json').exists():
    if time.monotonic()-start > 2700: raise SystemExit('Acquisition summary did not arrive within bounded wait')
    time.sleep(5)
assert json.loads((raw/'summary.json').read_text())['status'] == 'complete'
commands = [
    ('fit_models.py', ['--raw', str(raw), '--output', str(models)]),
    ('analyze.py', ['--raw', str(raw), '--models', str(models), '--output', str(analysis)]),
    ('figures.py', ['--analysis', str(analysis), '--raw', str(raw), '--models', str(models)]),
    ('verify.py', ['--raw', str(raw), '--models', str(models), '--analysis', str(analysis), '--output', str(analysis/'verification.json')]),
]
ledger = []
for script, args in commands:
    command = [sys.executable, str(base/script), *args]; began = time.perf_counter()
    record = dict(command=command, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with (base/(script.removesuffix('.py')+'.log')).open('x') as log:
        try:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=900)
            record['returncode'] = result.returncode
        except subprocess.TimeoutExpired:
            record['returncode'] = 'timeout'
    record['wall_s'] = time.perf_counter()-began; ledger.append(record)
    (base/'stages.json').write_text(json.dumps(ledger, indent=2)+'\n')
    print(script, record, flush=True)
    if record['returncode'] != 0: raise SystemExit('Failed stage retained; no downstream scoring')
