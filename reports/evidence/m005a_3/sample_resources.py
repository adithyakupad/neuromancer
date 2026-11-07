"""Read-only acquisition resource sampling; no model/selection decisions."""
import json
from pathlib import Path
import subprocess
import time

root=Path(__file__).resolve().parent
raw=root/'confirmation'
meta=json.loads((raw/'provenance.json').read_text())
progress=json.loads((raw/'supervision/progress.json').read_text())
pids=[w['pid'] for w in progress['workers'] if w.get('pid') and w.get('terminal') is None]
rss={}
if pids:
    result=subprocess.run(['ps','-o','pid=,rss=','-p',','.join(map(str,pids))],capture_output=True,text=True,timeout=2)
    for line in result.stdout.splitlines():
        pid,kib=map(int,line.split());rss[pid]=kib*1024
trials=[json.loads(p.read_text()) for p in raw.glob('n*_r*/trial.json')]
base=Path.cwd();roots=[p for p in (base/'reports/evidence').glob('m005a*') if p.is_dir()]
roots += [p for p in (base/'runs').glob('m005a-*') if p.is_dir()] if (base/'runs').exists() else []
allocated=sum(f.stat().st_blocks*512 for p in roots for f in p.rglob('*') if f.is_file() and not f.is_symlink())
record=dict(epoch_s=time.time(),monotonic_ns=time.monotonic_ns(),
            elapsed_s=(time.monotonic_ns()-meta['started_monotonic_ns'])/1e9,
            remaining_s=(meta['deadline_monotonic_ns']-time.monotonic_ns())/1e9,
            completed_trials=len(trials),published_branch_archives=sum(len(list(p.glob('*_*.npz'))) for p in raw.glob('n*_r*')),
            current_worker_rss_bytes=rss,completed_peak_rss_bytes=max([t['peak_rss_bytes'] for t in trials],default=0),
            allocated_m005a_evidence_and_runs_bytes=allocated,
            worker_faults=[str(p) for p in raw.glob('n*_r*/failure.json')])
with (root/'resource_samples.jsonl').open('a') as stream:stream.write(json.dumps(record)+'\n')
print(json.dumps(record))
if allocated>=500*1024**2 or any(v>=2*1024**3 for v in rss.values()) or record['completed_peak_rss_bytes']>=2*1024**3 or record['worker_faults']:
    raise SystemExit('RESOURCE/WORKER FAULT: stop qualification; do not replace trials')
