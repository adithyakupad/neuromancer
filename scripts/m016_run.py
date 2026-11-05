"""Execute frozen M016 workloads on the installed SDK simulator."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import sys
import time

os.environ['CL_SDK_ACCELERATED_TIME']='1'
os.environ['CL_SDK_VISUALISATION']='0'

from neuromancer.cl_adapter import CountPI,FIXTURE_MAP,SimulatorSession,verified_sdk
from neuromancer.clocks import now_ns
from neuromancer.neural_io import (BIN_FRAMES, ElectrodeRequest, FrameClock,
                                    SampleFrames, SpikeEvent, bin_frames)
from neuromancer.supervisor import Deadline,atomic_json


def run_case(output,name,enabled=True,delay=0):
    from cl.sim import clear_simulator_data_source,set_simulator_data_source
    sdk=verified_sdk()
    directory=output/name
    directory.mkdir()
    source_log=directory/'source.jsonl'
    set_simulator_data_source('neuromancer.cl_response_source:create_source',
        dict(seed=16016,enabled=enabled,extra_delay_frames=delay,audit_path=str(source_log)))
    deadline=Deadline.from_environment()
    rows=[]
    controller=CountPI() if name=='PI' else None
    session=SimulatorSession()
    elapsed=time.perf_counter()
    cpu=time.process_time()
    try:
        with session.open():
            neurons=session.neurons
            recording=neurons.record(file_suffix=name,file_location=str(directory),
                attributes={'m016_source':'m016-pulse-v1','m016_case':name})
            expected=None
            try:
                for index,current in enumerate(neurons.loop(50,stop_after_ticks=16)):
                    began=now_ns()
                    deadline.check()
                    analysis=current.analysis
                    start,stop=analysis.start_timestamp,analysis.stop_timestamp
                    if expected is None:
                        clock=FrameClock(name,start)
                        expected=start
                    events=tuple(SpikeEvent(spike.timestamp,spike.channel,
                                None if spike.samples is None else tuple(map(float,spike.samples)))
                                 for spike in analysis.spikes)
                    samples=SampleFrames(clock,start,stop,tuple(range(start,start+len(current.frames))),
                               tuple(range(64)),current.frames,.195)
                    observation=bin_frames(samples,events,FIXTURE_MAP,neurons.timestamp(),expected)
                    expected=stop
                    receipts=session.receipts(analysis.stims,stop)
                    if receipts and controller is not None:
                        controller.resolve(True)
                    proposal=(controller.propose(observation) if controller is not None and index<15
                              else name not in ('PI','C0','FROZEN') and (index in (2,5,8,11) or (name=='C6' and index==13)))
                    request=None
                    decision=None
                    submit_ns=None
                    if proposal:
                        late_fixture=name=='C6' and index==13
                        channel=1 if name=='C4' else 99 if name=='C6' and not late_fixture else 0
                        request=ElectrodeRequest(f'{name}-{index}',clock,channel,
                            stop-BIN_FRAMES if late_fixture else stop,
                            stop if late_fixture else stop+BIN_FRAMES)
                        submit_start=now_ns()
                        decision=session.submit(request,observation,clock)
                        submit_ns=now_ns()-submit_start
                        if not decision.accepted and controller is not None:
                            controller.resolve(False)
                    finished=now_ns()
                    rows.append(dict(index=index,start=start,stop=stop,available=observation.available_frame,
                        counts=observation.counts,valid=all(observation.valid),missing=observation.missing_frames,
                        late=observation.late,spikes=[(s.frame,s.electrode) for s in events],
                        request=asdict(request) if request else None,
                        decision=asdict(decision) if decision else None,
                        receipts=[asdict(receipt) for receipt in receipts],application_ns=finished-began,
                        tick_began_ns=began,submit_started_ns=submit_start if proposal else None,
                        submit_ns=submit_ns,pi_integral=controller.integral if controller else None))
                    deadline.check()
                if session.pending is not None:
                    raise RuntimeError('Unresolved stimulation at end of session')
            finally:
                recording.stop()
                recording.wait_until_stopped()
                atomic_json(directory/'ticks.json',rows)
        with sdk.RecordingView(recording.file['path']) as view:
            recorded=dict(shape=list(view.samples.shape),spikes=len(view.spikes),
                stims=len(view.stims),source=view.attributes['application']['m016_source'])
        deadline.check()
        summary=dict(case=name,recording=recorded,elapsed_s=time.perf_counter()-elapsed,
                     cpu_s=time.process_time()-cpu,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        atomic_json(directory/'summary.json',summary)
        return summary
    finally:
        clear_simulator_data_source()


def main(output,mode):
    verified_sdk()
    if mode=='smoke':
        cases=[('SMOKE',True,0)]
    elif mode=='matrix':
        cases=[('C0',True,0),('C1',True,0),('C2',False,0),('C4',True,0),('C5',True,700),
               ('C6',True,0),('PI',True,0),('FROZEN',True,0),('C1_REPEAT',True,0)]
    else:
        raise ValueError('Unknown workload')
    completed=[]
    for name,enabled,delay in cases:
        completed.append(run_case(output,name,enabled,delay))
        if sum(path.stat().st_size for path in output.rglob('*') if path.is_file())>25*1024**2:
            raise RuntimeError('Recording storage cap exceeded')
        atomic_json(output/'completed.json',completed)


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve(),sys.argv[2])
