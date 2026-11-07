"""Three-worker, nonreserved scheduling benchmark; no tracking metrics."""
import sys,time,json
from pathlib import Path
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config
from neuromancer.calibration import prefix_schedule
from neuromancer.diagnostic import schedule,peak_rss_bytes
from neuromancer.predictive import initialize,PredictiveController
from neuromancer.tick_execution import TickExecution
from neuromancer.supervisor import Deadline,atomic_json
R=Path(__file__).resolve().parent

def main():
 label=sys.argv[1];kind=label.split('_')[0];d=Deadline.from_environment();d.check();began=time.perf_counter();e=BrianEngine(Config(network_id=0,replicate_id=60,trial_id='v1-concurrency-'+kind))
 try:
  pref=e.run_commands(schedule(e,prefix_schedule()));initial=initialize([x.observation for x in pref],[x.receipt for x in pref]);driver=TickExecution(e);controller=PredictiveController(initial,kind);start=time.perf_counter();records=driver.run(controller,8,deadline=d);control=time.perf_counter()-start
  assert controller.failure is None and len(records)==400
  atomic_json(R/f'concurrent_four_{label}.json',dict(kind=kind,status='PASS',simulated_seconds=59,control_simulated_seconds=8,control_wall_s=control,total_wall_s=time.perf_counter()-began,peak_rss_bytes=peak_rss_bytes(),planner_ns=[p['elapsed_ns'] for p in controller.plans],deadline_misses=0,study_outcomes_computed=False))
 finally:e.close()
if __name__=='__main__':main()
