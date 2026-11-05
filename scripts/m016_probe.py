"""Inspect installed public SDK and run a bounded read-only default probe."""
import inspect
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import resource
import sys
import time

os.environ['CL_SDK_ACCELERATED_TIME']='1'
os.environ['CL_SDK_VISUALISATION']='0'

import cl
import cl.sim
import psutil
from neuromancer.supervisor import Deadline,atomic_json

output=Path(sys.argv[1])
deadline=Deadline.from_environment()
signatures={}
for owner,names in [(cl,['open','is_simulator','ChannelSet','StimDesign','RecordingView']),
                    (cl.Neurons,['read','stim','loop','record']),
                    (cl.sim,['SimulatorDataSourceMetadata','DataSourceBatch','DataSourceSpike',
                             'DataSourceStim','set_simulator_data_source']),
                    (cl.sim.SimulatorDataSource,['open','close','read','on_stim','on_stims'])]:
    for name in names:
        signatures[f'{owner.__name__}.{name}']=str(inspect.signature(getattr(owner,name)))
atomic_json(output/'signatures.json',dict(version=metadata.version('cl-sdk'),python=sys.version,
    module=str(cl.__file__),simulator=cl.is_simulator(),signatures=signatures))
if cl.is_simulator() is not True:
    raise RuntimeError('HARDWARE_UNQUALIFIED')
deadline.check()
started=time.perf_counter()
cpu=time.process_time()
with cl.open(take_control=False) as neurons:
    startup=time.perf_counter()-started
    before=time.perf_counter()
    frames=neurons.read(2000)
    read_s=time.perf_counter()-before
    children=[dict(pid=child.pid,created=child.create_time(),rss_bytes=child.memory_info().rss)
              for child in psutil.Process().children(recursive=True)]
    result=dict(startup_s=startup,read_s=read_s,shape=list(frames.shape),
        dtype=str(frames.dtype),frames_per_second=neurons.get_frames_per_second(),children=children)
deadline.check()
result.update(elapsed_s=time.perf_counter()-started,cpu_s=time.process_time()-cpu,
              peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
atomic_json(output/'probe.json',result)
