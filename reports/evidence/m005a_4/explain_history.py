"""Read-only reconstruction of the historical clock comparison."""
import json
from pathlib import Path
r=Path('reports/evidence/m005a_4');old=Path('reports/evidence/m005a_3')
meta=json.loads((old/'confirmation/provenance.json').read_text());closure=json.loads((old/'acquisition_closure.json').read_text())
rows=[]
for line in (old/'resource_samples.jsonl').read_text().splitlines():
    x=json.loads(line);calendar=x['epoch_s']-meta['started_epoch_s'];active=x['elapsed_s']
    rows.append(dict(epoch_s=x['epoch_s'],calendar_elapsed_s=calendar,awake_elapsed_s=active,
                     residual_s=calendar-active,delta_residual_s=None if not rows else calendar-active-rows[-1]['residual_s']))
assert max(x['residual_s'] for x in rows)-min(x['residual_s'] for x in rows)>30
assert closure['calendar_duration_s']<5400 and closure['monotonic_duration_s']<5400
r.joinpath('historical_clock_analysis.json').write_text(json.dumps(dict(
    clocks=dict(calendar='CLOCK_REALTIME via time.time()',awake='mach_absolute_time via CPython monotonic/perf_counter'),
    samples=rows,largest_intersample_offset_step_s=max(x['delta_residual_s'] or 0 for x in rows),
    calendar_duration_s=closure['calendar_duration_s'],awake_duration_s=closure['monotonic_duration_s'],
    observed_deadline_exceeded=False,primary_explanation='Different documented suspend semantics, temporally corroborated by OS clamshell log',
    limits='Historical continuous clock was not measured; minor wall-clock correction/measurement skew cannot be excluded. Old epoch start was captured after setup, so initial offset is not a suspend estimate.',
    old_stop_decision='Preserved: required by the then-frozen discrepancy gate',new_scientific_acquisition=False),indent=2)+'\n')
