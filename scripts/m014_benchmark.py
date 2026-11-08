"""Fixed development timing probe; no classification or reserved outcomes."""
import json
from pathlib import Path
import resource
import sys
import time
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.reservoir import commands_for_trial,reset_trial
from neuromancer.supervisor import atomic_json,Deadline

output=Path(sys.argv[1])
deadline=Deadline.from_environment()
start=time.perf_counter()
engine=BrianEngine(Config(network_id=14000,root_seed=20261105,trial_id='benchmark'))
construction=time.perf_counter()-start
measurements=[]
try:
    for replicate in [149000,149001,149002]:
        deadline.check()
        start=time.perf_counter()
        reset_trial(engine,replicate,True)
        result=engine.run_commands(commands_for_trial(0,1,80,'benchmark'))
        measurements.append(time.perf_counter()-start)
        atomic_json(output/'partial.json',dict(trials_s=measurements,construction_s=construction))
    maximum=max(measurements)
    pilot=2*(4*construction+640*maximum+20.48*maximum/.36)+60
    confirmation=2*(128*construction+114688*maximum)+60
    atomic_json(output/'benchmark.json',dict(construction_s=construction,trials_s=measurements,
        pilot_forecast_s=pilot,pilot_budget_s=900,confirmation_forecast_s=confirmation,
        confirmation_budget_s=3600,pilot_gate='PASS' if pilot<=900 else 'HOLD',
        confirmation_gate='PASS' if confirmation<=3600 else 'NOT RUN',
        max_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,simulated_seconds=1.08))
finally:engine.close()
