"""Importable CL SDK synthetic pulse-response source."""
import json
from pathlib import Path
import time

import numpy as np
from cl.sim import DataSourceBatch, DataSourceSpike, SimulatorDataSource, SimulatorDataSourceMetadata


class PulseSource(SimulatorDataSource):
    metadata = SimulatorDataSourceMetadata(channel_count=64,seekable=False)
    identity = 'm016-pulse-v1'

    def __init__(self, seed, enabled, extra_delay_frames, audit_path):
        if type(seed) is not int or not 0 <= seed < 2**32 or type(enabled) is not bool:
            raise ValueError('Invalid source seed or response flag')
        if type(extra_delay_frames) is not int or extra_delay_frames not in (0,700):
            raise ValueError('Invalid fixture delay')
        self.path = Path(audit_path)
        if not self.path.is_absolute() or not self.path.parent.is_dir():
            raise ValueError('Source audit path must be absolute in a prepared directory')
        self.phase = int(np.random.default_rng(seed).integers(100,200))
        self.enabled = enabled
        self.delay = extra_delay_frames
        self.audit = None
        self.pending = set()
        self.stop = None
        self.collisions = 0
        self.m018_trace = self.path.parent.name == 'FROZEN'

    def _log(self, **event):
        self.audit.write(json.dumps(event)+'\n')
        self.audit.flush()

    def _trace(self, kind, **details):
        if self.m018_trace:
            self._log(kind=kind, host_monotonic_ns=time.monotonic_ns(),
                      frame_clock='sdk_frame_index', **details)

    def open(self):
        self.audit = self.path.open('x')
        self._log(kind='open',source=self.identity,phase=self.phase,
                  enabled=self.enabled,extra_delay_frames=self.delay)
        self._trace('m018_source_open')

    def close(self):
        if self.audit is not None:
            self._trace('m018_source_close_begin',last_stop=self.stop)
            self._log(kind='close',pending=len(self.pending),collisions=self.collisions)
            self.audit.close()
            self.audit = None

    def on_stim(self, stim):
        self._trace('m018_stim_begin',frame=stim.timestamp)
        self._log(kind='commit',frame=stim.timestamp,electrode=stim.channel,
                  intended=stim.intended_timestamp,durations_us=stim.phase_durations_us,
                  currents_uA=stim.phase_currents_uA)
        if not self.enabled or stim.channel != 4:
            self._trace('m018_stim_end',frame=stim.timestamp,queued=len(self.pending))
            return
        for offset in (100,150,200):
            frame = stim.timestamp+offset+self.delay
            if self.stop is not None and frame < self.stop:
                raise RuntimeError('Synthetic response arrived after read head')
            self.pending.add(frame)
        if len(self.pending)>4096:
            raise RuntimeError('Synthetic response queue limit exceeded')
        self._trace('m018_stim_end',frame=stim.timestamp,queued=len(self.pending))

    def read(self, from_timestamp, frame_count):
        self._trace('m018_read_begin',start=from_timestamp,count=frame_count,
                    previous_stop=self.stop)
        if self.stop is not None and from_timestamp != self.stop:
            raise ValueError('Discontinuous source read')
        stop = from_timestamp+frame_count
        baseline = {frame for frame in range(from_timestamp,stop) if frame%500==self.phase}
        emitted = {frame for frame in self.pending if from_timestamp<=frame<stop}
        self.pending.difference_update(emitted)
        self.collisions += len(baseline & emitted)
        self.stop = stop
        batch = DataSourceBatch(frames=np.zeros((frame_count,64),dtype=np.int16),
            spikes=[DataSourceSpike(timestamp=frame,channel=8) for frame in sorted(baseline|emitted)])
        self._trace('m018_read_end',start=from_timestamp,stop=stop,
                    count=frame_count,spike_count=len(baseline|emitted))
        return batch


def create_source(seed,enabled,extra_delay_frames,audit_path):
    return PulseSource(seed,enabled,extra_delay_frames,audit_path)
