"""M003.1 registered schedule adapter to the unchanged six-branch M003 runner."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed,TimeoutError
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import time
import numpy as np
from . import identification_experiment as acquisition
from .calibration import ramp
from .diagnostic import provenance
from .calibration_diagnostic import save_json
from .substrate import Config

NAMES=('S','SHORT','LONG','NEAR','FAR','R')
PAIRS=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))


def schedules(config):
    prefix=np.vstack([np.zeros((750,4)),acquisition.excitation(config,4,0),acquisition.excitation(config,1,1),acquisition.excitation(config,1,2),np.zeros((200,4))])
    desired=np.zeros((6,100,4));pair=list(PAIRS[(config.network_id+config.replicate_id-22)%6])
    for a,start,stop,value in ((1,0,5,120),(2,0,20,30),(3,0,5,60),(3,10,15,60),(4,0,5,60),(4,30,35,60)):
        desired[a,start:stop,pair]=value
    random=acquisition.excitation(config,1,4)[:100]
    for slot,hold in enumerate((6,12,18,20)):
        desired[5,slot*25+5:slot*25+5+hold]=random[slot*25+5:slot*25+5+hold]
    planned=np.array([ramp(x) for x in desired]);delivered_prefix=ramp(prefix)
    for x in (delivered_prefix,*planned):assert acquisition.audit(x)['violations']==0
    for x in planned[1:5]:assert abs(x.sum()*.02-24)<1e-12
    assert not delivered_prefix[-1].any()
    return prefix,delivered_prefix,desired,planned


def worker(n,r,g,output):
    # The existing runner fixes six branches and clocks; only registered plans/names differ per spawned process.
    acquisition.schedules=schedules;acquisition.NAMES=NAMES
    return acquisition.run_trial(n,r,g,output,None)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS'):os.environ[key]='1'
    jobs=[(n,r,1.) for n in range(10) for r in (22,23,24)]+[(n,25,0.) for n in range(3)]
    protocol=Path('docs/research/006_M003_1_MODEL_NECESSITY_PROTOCOL.md');record=provenance()
    record.update(mission='M003.1',jobs=jobs,simulated_seconds=2607,wall_limit_s=2700,preregistration_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),conditions=NAMES,
        evaluated_split='development0-9, new noise22-24; null0-2 noise25; no validation/test acquisition')
    save_json(a.output/'provenance.json',record);start=time.perf_counter_ns();results=[]
    with ProcessPoolExecutor(max_workers=3,mp_context=mp.get_context('spawn')) as pool:
        futures=[pool.submit(worker,n,r,g,str(a.output)) for n,r,g in jobs]
        try:
            for future in as_completed(futures,timeout=2700):
                result=future.result();results.append(result);save_json(a.output/'progress.json',results);print(f'{len(results)}/33 {result}',flush=True)
        except TimeoutError:
            for process in pool._processes.values():process.terminate()
            raise SystemExit('Acquisition cap reached; partial evidence preserved')
    hashes={str(f.relative_to(a.output)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(a.output.rglob('*')) if f.is_file()}
    save_json(a.output/'summary.json',dict(status='complete' if all(v['status']=='complete' for v in results) else 'partial',trials=results,wall_ns=time.perf_counter_ns()-start,artifact_sha256=hashes))
    if len(results)!=33 or any(v['status']!='complete' for v in results):raise SystemExit('Incomplete fixed cohort')


if __name__=='__main__':main()
