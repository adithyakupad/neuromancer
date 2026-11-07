"""One predeclared one-second resource probe, never a learning experiment."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

if sys.argv[1] == '--worker':
    from neuromancer.plasticity import PlasticReservoir
    from neuromancer.substrate import Config, Command
    from neuromancer.supervisor import atomic_json
    output = Path(sys.argv[2])
    started = time.perf_counter()
    reservoir = PlasticReservoir(Config(network_id=13000,replicate_id=1300,root_seed=20261104,trial_id='benchmark'))
    initialization = time.perf_counter()-started
    atomic_json(output/'partial.json',{'initialized':True,'initialization_s':initialization})
    commands = [Command('benchmark',str(i),i*20000,(0.,0.,0.,0.)) for i in range(50)]
    started = time.perf_counter()
    results = reservoir.engine.run_commands(commands)
    elapsed = time.perf_counter()-started
    forecast = 2*(10*initialization+179.2*elapsed)+60
    atomic_json(output/'benchmark.json',dict(initialization_s=initialization,simulation_s=elapsed,
        simulated_s=1,forecast_s=forecast,budget_s=900,forecast_gate='PASS' if forecast<=900 else 'HOLD',
        synapses=len(reservoir.indices),trace_array_bytes=4*8*len(reservoir.indices),
        max_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        neural_records=len(results),training=False))
    reservoir.close()
else:
    from neuromancer.supervisor import Deadline, supervise
    output = Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=False)
    result = supervise([[sys.executable,__file__,'--worker',str(output)]], output/'supervision',Deadline.after(120),workers=1)
    (output/'returned.json').write_text(json.dumps(result,indent=2))
    if result['status'] != 'COMPLETED':
        raise SystemExit('Resource qualification HOLD')
