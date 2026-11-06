"""Simulator-only producer-boundary diagnostic with one changed factor per condition."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from neuromancer.cl_adapter import CountPI, FIXTURE_MAP, SimulatorSession, verified_sdk
from neuromancer.neural_io import ElectrodeRequest, FrameClock, SampleFrames, SpikeEvent, bin_frames
from neuromancer.supervisor import Deadline

CONDITIONS = ('stock', 'custom', 'record', 'replay', 'pi')


def mark(log, event, **fields):
    log.write(json.dumps(dict(event=event, host_ns=time.monotonic_ns(), **fields)) + '\n')


@contextmanager
def observer(neurons, output):
    # SDK 1.0.0 private handles provide only the locator and PID.
    header = neurons._shared_buffer._shm_header
    producer = neurons._data_producer._process
    command = [sys.executable, str(Path(__file__).with_name('m019_observe.py')),
               header.name, str(producer.pid), str(output)]
    process = subprocess.Popen(command)
    try:
        ready_until = time.monotonic() + 2
        while not (output / 'observer.ready').exists():
            if process.poll() is not None or time.monotonic() >= ready_until:
                raise RuntimeError('Observer did not become ready')
            time.sleep(.005)
        yield
    finally:
        (output / 'observer.stop').touch()
        try:
            status = process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)
            raise RuntimeError('Observer needed forced cleanup')
        if status:
            raise RuntimeError(f'Observer failed with exit {status}')


def session_probe(sdk, output, condition, deadline):
    from cl.sim import clear_simulator_data_source, set_simulator_data_source

    if condition != 'stock':
        set_simulator_data_source('neuromancer.cl_response_source:create_source', {
            'seed': 16016, 'enabled': True, 'extra_delay_frames': 0,
            'audit_path': str(output / 'source.jsonl'), 'trace': True,
        })
    session = SimulatorSession()
    controller = CountPI() if condition == 'pi' else None
    pulse_count = 0
    try:
        with (output / 'client.jsonl').open('x', buffering=1) as log:
            mark(log, 'open_begin')
            with session.open():
                neurons = session.neurons
                origin = neurons.timestamp()
                clock = FrameClock('m019', origin)
                mark(log, 'open_end', origin=origin)
                recording = None
                if condition in ('record', 'replay', 'pi'):
                    mark(log, 'record_begin')
                    recording = neurons.record(file_location=str(output), file_suffix='m019')
                    mark(log, 'record_ready')
                try:
                    with observer(neurons, output):
                        ticks = iter(neurons.loop(50, stop_after_ticks=16))
                        try:
                            for index in range(16):
                                deadline.check()
                                start = origin + 500 * index
                                stop = start + 500
                                mark(log, 'next_begin', target=stop)
                                try:
                                    tick = next(ticks)
                                except Exception as error:
                                    mark(log, 'next_failed', target=stop, error=repr(error))
                                    raise
                                mark(log, 'next_end', target=stop, count=len(tick.frames))
                                analysis = tick.analysis
                                if (analysis.start_timestamp, analysis.stop_timestamp) != (start, stop):
                                    raise RuntimeError('Unexpected SDK frame interval')
                                samples = SampleFrames(clock, start, stop, tuple(range(start, stop)),
                                                       tuple(range(64)), tick.frames, .195)
                                spikes = tuple(SpikeEvent(s.timestamp, s.channel) for s in analysis.spikes)
                                observation = bin_frames(samples, spikes, FIXTURE_MAP,
                                                         neurons.timestamp(), start)
                                if observation.late or not all(observation.valid):
                                    raise RuntimeError('Unexpected observation validity')
                                receipts = session.receipts(analysis.stims, stop)
                                pulse_count += len(receipts)
                                if receipts and controller is not None:
                                    controller.resolve(True)
                                if controller is not None:
                                    proposal = index < 15 and controller.propose(observation)
                                else:
                                    proposal = condition == 'replay' and index % 2 == 0
                                if proposal:
                                    request = ElectrodeRequest(str(index), clock, 0, stop, stop + 500)
                                    if not session.submit(request, observation, clock).accepted:
                                        raise RuntimeError('Fixture pulse rejected')
                                mark(log, 'processed', target=stop, receipts=len(receipts))
                            if next(ticks, None) is not None or session.pending is not None:
                                raise RuntimeError('Unexpected final tick or unresolved pulse')
                        finally:
                            ticks.close()
                finally:
                    if recording is not None:
                        mark(log, 'record_stop_begin')
                        recording.stop()
                        recording.wait_until_stopped()
                        mark(log, 'record_stop_end')
            mark(log, 'close_end')
        expected = 8 if condition in ('replay', 'pi') else 0
        if pulse_count != expected:
            raise RuntimeError('Unexpected receipt count')
        if recording is not None:
            with sdk.RecordingView(recording.file['path']) as view:
                if view.samples.shape != (8000, 64) or len(view.stims) != expected:
                    raise RuntimeError('Unexpected completed recording')
        deadline.check()
    finally:
        clear_simulator_data_source()


def main(output, condition, sessions):
    if condition not in CONDITIONS or (sessions != 3 and (condition, sessions) != ('stock', 1)):
        raise ValueError('Unplanned diagnostic condition')
    os.environ['CL_SDK_ACCELERATED_TIME'] = '1'
    os.environ['CL_SDK_VISUALISATION'] = '0'
    os.environ.pop('CL_SDK_REPLAY_PATH', None)
    sdk = verified_sdk()
    deadline = Deadline.from_environment()
    for index in range(sessions):
        directory = output / f'session-{index}'
        directory.mkdir()
        session_probe(sdk, directory, condition, deadline)
        (directory / 'complete').touch()


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], int(sys.argv[3]))
