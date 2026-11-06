"""Standalone accelerated CL SDK fixture. Requires only cl-sdk and numpy."""
from importlib import metadata
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import cl
from cl.sim import DataSourceBatch, DataSourceSpike, SimulatorDataSource, SimulatorDataSourceMetadata


class Source(SimulatorDataSource):
    metadata = SimulatorDataSourceMetadata(channel_count=64, seekable=False)

    def read(self, from_timestamp, frame_count):
        stop = from_timestamp + frame_count
        frames = np.zeros((frame_count, 64), dtype=np.int16)
        frames[:, 0] = np.arange(from_timestamp, stop)
        spikes = [DataSourceSpike(timestamp=frame, channel=8)
                  for frame in range(from_timestamp, stop) if frame % 500 in (0, 499)]
        return DataSourceBatch(frames=frames, spikes=spikes)


def make_source():
    return Source()


def mark(log, event, **fields):
    log.write(json.dumps(dict(event=event, host_ns=time.monotonic_ns(), **fields)) + '\n')


def probe(directory, mode):
    cl.sim.set_simulator_data_source('probe:make_source')
    os.environ['RECOVER_PRODUCER_TRACE'] = str(directory / 'producer.csv')
    with (directory / 'client.jsonl').open('x', buffering=1) as log:
        try:
            with cl.open() as neurons:
                origin = neurons.timestamp()
                target = origin + 8000
                cap = dict(stop_after_frames=8000) if mode == 'bounded' else {}
                recording = neurons.record(file_location=str(directory), file_suffix=mode,
                                           attributes={'expected_final_frame': target}, **cap)
                ticks = iter(neurons.loop(50, stop_after_ticks=16))
                try:
                    for index in range(16):
                        start = origin + 500 * index
                        stop = start + 500
                        mark(log, 'next_begin', target=stop)
                        tick = next(ticks)
                        a = tick.analysis
                        assert (a.start_timestamp, a.stop_timestamp) == (start, stop)
                        np.testing.assert_array_equal(tick.frames[:, 0], np.arange(start, stop))
                        assert [s.timestamp for s in a.spikes] == [start, stop - 1]
                        mark(log, 'consumed', stop=stop)
                    if mode == 'before':
                        recording.stop()
                        recording.wait_until_stopped()
                    assert next(ticks, None) is None
                    if mode == 'bounded':
                        recording.wait_until_stopped()
                    elif mode != 'before':
                        # Fixed opportunity for final prefetch to reach the recorder.
                        time.sleep(.03)
                        recording.stop()
                        recording.wait_until_stopped()
                    mark(log, 'recording_stopped', head=neurons.timestamp())
                finally:
                    ticks.close()
                    recording.stop()
            with cl.RecordingView(recording.file['path']) as view:
                count = int(view.samples.shape[0])
                np.testing.assert_array_equal(view.samples[:, 0], np.arange(origin, origin + count))
                events = [int(event['timestamp']) + origin for event in view.spikes]
                expected = [frame for frame in range(origin, origin + count) if frame % 500 in (0, 499)]
                assert events == expected and len(view.stims) == 0
                assert view.attributes['application']['expected_final_frame'] == target
                actual_end = int(view.attributes['end_timestamp'])
                mark(log, 'recording_verified', origin=origin, expected_final_frame=target,
                     recorded=count, actual_end=actual_end, spikes=len(events))
                assert actual_end == origin + count
                if mode in ('before', 'bounded'):
                    assert count == 8000
        except Exception as error:
            mark(log, 'failed', error=repr(error))
            raise
        finally:
            cl.sim.clear_simulator_data_source()


def main(output, mode, sessions):
    if metadata.version('cl-sdk') != '1.0.0' or cl.is_simulator() is not True:
        raise RuntimeError('Requires the qualified SDK simulator identity')
    for index in range(sessions):
        directory = output / f'session-{index}'
        directory.mkdir()
        probe(directory, mode)
        (directory / 'complete').touch()


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], int(sys.argv[3]))
