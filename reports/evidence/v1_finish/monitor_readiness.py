"""Progress and mandatory safety only; does not read tracking outcomes."""
import datetime,json
from pathlib import Path
B=Path('reports/evidence/v1_finish/m005b');s=json.loads((B/'primary_resource.jsonl').read_text().splitlines()[-1]);launch=json.loads((B/'primary_launch.json').read_text());p=[json.loads(f.read_text()) for f in (B/'primary').glob('n*_r*/progress.json')];bad=[];checked=0
for path in (B/'primary').glob('n*_r*/trial.json'):
 t=json.loads(path.read_text())
 for branch in t['branches']:
  checked+=1
  if branch['safe_bins'] or branch['violations'] or branch['model_failure']:bad.append(dict(trial=path.parent.name,branch=branch['name'],safe_bins=branch['safe_bins'],violations=branch['violations'],model_failure=branch['model_failure']))
result=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_s=round((s['ns']-launch['started_ns'])/1e9),complete_trials=s['complete_trials'],complete_branches=sum(x['complete_branches'] for x in p),safety_checked_branches=checked,safety_failures=bad,rss_GiB=round(s['aggregate_rss_bytes']/2**30,2),allocated_MiB=round(s['mission_allocated_bytes']/2**20,1),worker_failures=s['failures'],tracking_outcomes_inspected=False)
with (B/'readiness_monitor.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
print(json.dumps(result));raise SystemExit(2 if bad or s['failures'] else 0)
