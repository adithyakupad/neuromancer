"""Typed sample-clock and electrode boundary for MEA input and output."""
from dataclasses import dataclass
from enum import Enum
from math import isfinite

import numpy as np

FRAME_HZ = 25_000
FRAME_US = 40
BIN_FRAMES = 500
MAX_TIMESTAMP = (1 << 63) - 1


def tick(value):
    if type(value) is not int or not 0 <= value <= MAX_TIMESTAMP:
        raise ValueError('Expected a nonnegative signed-64-bit integer timestamp')
    return value


@dataclass(frozen=True)
class FrameClock:
    session_id: str
    origin_frame: int

    def __post_init__(self):
        tick(self.origin_frame)
        if not isinstance(self.session_id, str) or not self.session_id:
            raise ValueError('Clock requires a session identity')

    def relative_us(self, frame: int) -> int:
        relative = tick(frame) - self.origin_frame
        return tick(relative * FRAME_US)

    def frame_at(self, relative_us: int) -> int:
        offset, remainder = divmod(tick(relative_us), FRAME_US)
        if remainder:
            raise ValueError('Timestamp is not on a frame boundary')
        return tick(self.origin_frame + offset)

    def bin_at(self, frame: int) -> int:
        return self.relative_us(frame) // (FRAME_US * BIN_FRAMES)


@dataclass(frozen=True)
class ChannelMap:
    electrode_count: int
    stimulation: tuple[int, ...]
    recording: tuple[int, ...]
    allowed_stimulation: tuple[int, ...]
    geometry_um: tuple[tuple[float, float], ...] | None = None

    def __post_init__(self):
        if type(self.electrode_count) is not int or self.electrode_count <= 0:
            raise ValueError('Invalid electrode count')
        for channels in (self.stimulation, self.recording, self.allowed_stimulation):
            if any(type(channel) is not int or not 0 <= channel < self.electrode_count
                   for channel in channels) or len(set(channels)) != len(channels):
                raise ValueError('Invalid or duplicate electrode')
        if len(self.stimulation) != 4 or len(self.recording) != 20:
            raise ValueError('Expected four stimulation and twenty recording mappings')
        if not set(self.stimulation) <= set(self.allowed_stimulation):
            raise ValueError('Unsupported stimulation electrode')
        if set(self.stimulation) & set(self.recording):
            raise ValueError('Fixture requires disjoint stimulation and recording')
        if self.geometry_um is not None and (
            len(self.geometry_um) != self.electrode_count
            or any(len(point) != 2 or not all(isfinite(value) for value in point)
                   for point in self.geometry_um)
            or len(set(self.geometry_um)) != self.electrode_count
        ):
            raise ValueError('Invalid or ambiguous electrode geometry')


@dataclass(frozen=True)
class SpikeEvent:
    frame: int
    electrode: int
    waveform_uV: tuple[float, ...] | None = None


@dataclass(frozen=True)
class SampleFrames:
    clock: FrameClock
    start: int
    stop: int
    indices: tuple[int, ...]
    electrode_ids: tuple[int, ...]
    samples: np.ndarray
    sample_unit_uV: float
    frames_per_second: int = FRAME_HZ


@dataclass(frozen=True)
class SpikeBin:
    clock: FrameClock
    start: int
    stop: int
    available_frame: int
    counts: tuple[int, ...]
    valid: tuple[bool, ...]
    missing_frames: int
    late: bool


def bin_frames(frames: SampleFrames, spikes: tuple[SpikeEvent, ...], mapping: ChannelMap,
               available_frame: int, expected_start: int) -> SpikeBin:
    start, stop, available = map(tick, (frames.start, frames.stop, available_frame))
    frames.clock.relative_us(start)
    frames.clock.relative_us(stop)
    frames.clock.relative_us(available)
    if start != tick(expected_start) or stop-start != BIN_FRAMES or available < stop:
        raise ValueError('Discontinuous or incomplete observation interval')
    if (frames.frames_per_second != FRAME_HZ or not isfinite(frames.sample_unit_uV)
            or frames.sample_unit_uV <= 0 or frames.electrode_ids != tuple(range(mapping.electrode_count))
            or not isinstance(frames.samples, np.ndarray) or frames.samples.dtype != np.int16
            or frames.samples.shape != (len(frames.indices), mapping.electrode_count)):
        raise ValueError('Invalid sample metadata, dimensions or dtype')
    previous = start-1
    for index in frames.indices:
        if not previous < tick(index) < stop:
            raise ValueError('Duplicate or nonmonotonic sample frame')
        previous = index
    counts = [0]*len(mapping.recording)
    lookup = {electrode: index for index, electrode in enumerate(mapping.recording)}
    previous_frame = start
    seen = set()
    for event in spikes:
        frame = tick(event.frame)
        if not previous_frame <= frame < stop:
            raise ValueError('Late, future or nonmonotonic spike')
        if type(event.electrode) is not int or not 0 <= event.electrode < mapping.electrode_count:
            raise ValueError('Invalid spike electrode')
        if event.waveform_uV is not None and (
            len(event.waveform_uV) != 75 or not all(isfinite(sample) for sample in event.waveform_uV)
        ):
            raise ValueError('Invalid spike waveform')
        key = (frame,event.electrode)
        if key in seen:
            raise ValueError('Duplicate spike')
        seen.add(key)
        previous_frame = frame
        if event.electrode in lookup:
            counts[lookup[event.electrode]] += 1
    missing = BIN_FRAMES-len(frames.indices)
    late = available-stop >= BIN_FRAMES
    return SpikeBin(frames.clock,start,stop,available,tuple(counts),
                    (not missing and not late,)*len(counts),missing,late)


@dataclass(frozen=True)
class ElectrodeRequest:
    request_id: str
    clock: FrameClock
    logical_channel: int
    observation_stop: int
    expires_frame: int
    lead_us: int = 80
    phases_us_uA: tuple[tuple[int, float], ...] = ((160,-1.),(160,1.))


@dataclass(frozen=True)
class StimDecision:
    request_id: str
    accepted: bool
    reason: str
    electrode: int | None = None
    submitted_frame: int | None = None


@dataclass(frozen=True)
class StimReceipt:
    request_id: str
    clock: FrameClock
    electrode: int
    committed_frame: int


class SessionState(str, Enum):
    CLOSED = 'closed'
    OPEN_SIMULATOR = 'open_simulator'
    HARDWARE_UNQUALIFIED = 'hardware_unqualified'


def validate_stim(request, observation, clock, mapping, now_frame):
    now = tick(now_frame)
    if request.clock != clock or observation.clock != clock:
        raise ValueError('Foreign session clock')
    if not request.request_id or not all(observation.valid) or observation.late:
        raise ValueError('Missing or invalid observation')
    if type(request.lead_us) is not int or request.lead_us != 80:
        raise ValueError('Unsupported lead time')
    if (tick(request.observation_stop) != observation.stop
            or not observation.available_frame <= now < tick(request.expires_frame)
            or request.expires_frame != observation.stop+BIN_FRAMES
            or now + request.lead_us//FRAME_US >= request.expires_frame):
        raise ValueError('Late or mismatched request')
    if type(request.logical_channel) is not int or not 0 <= request.logical_channel < 4:
        raise ValueError('Unsupported stimulation destination')
    if request.phases_us_uA != ((160,-1.),(160,1.)):
        raise ValueError('Unsupported simulator pulse design')
    return mapping.stimulation[request.logical_channel]
