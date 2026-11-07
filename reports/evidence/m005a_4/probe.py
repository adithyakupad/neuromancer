"""Native uninterrupted API/ABI probe; does not simulate or initiate OS sleep."""
import csv
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from neuromancer.clocks import get_clock

r=Path(__file__).resolve().parent;c=get_clock();samples=[];cost=[]
for _ in range(1000):
    began=time.perf_counter_ns();s=c.sample();cost.append(time.perf_counter_ns()-began);samples.append(s)
assert all(x['continuous_ns']<=y['continuous_ns'] for x,y in zip(samples,samples[1:]))
code='from neuromancer.clocks import get_clock;import json;print(json.dumps(get_clock().sample()))'
child=json.loads(subprocess.check_output([sys.executable,'-c',code],text=True))
assert child['clock_id']==c.domain and child['continuous_ns']>=samples[-1]['continuous_ns']
rows=list(csv.DictReader((r/'native_clock_probe.csv').open()))
assert len(rows)==20
for row in rows:
 d={k:int(v) for k,v in row.items()}
 assert d['continuous_before_ns']<=d['raw_ns']<=d['continuous_after_ns']
 assert d['absolute_ns']<=d['uptime_raw_ns']<=d['continuous_after_ns']
report=dict(status='PASS_NATIVE_API_COMPATIBILITY',basis='Apple authoritative suspend semantics plus native C/Python API execution; not a controlled sleep test',
            physical_sleep_test='NOT_RUN: controlled machine access unavailable; no power-state command issued',
            clock_id=c.domain,first=samples[0],last=samples[-1],cross_process_sample=child,
            native_c_rows=20,python_samples=1000,platform=platform.platform(),python=sys.version,
            clock_read_cost_ns=dict(min=min(cost),median=statistics.median(cost),p95=sorted(cost)[949],max=max(cost)),
            active_python_clock=vars(time.get_clock_info('monotonic')))
(r/'native_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
