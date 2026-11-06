"""Simulator-only CL SDK bridge, with a hardware-disabled entry point."""

from contextlib import contextmanager
from importlib import import_module, metadata
from pathlib import Path

from .neural_io import ChannelMap, FRAME_HZ, SessionState, StimDecision, StimReceipt, validate_stim

FIXTURE_MAP = ChannelMap(64, (4, 5, 6, 7), tuple(range(8, 28)), (4, 5, 6, 7))


def require_simulator(sdk):
    try:
        verified = sdk.is_simulator() is True
    except Exception:
        verified = False
    if not verified:
        raise RuntimeError(SessionState.HARDWARE_UNQUALIFIED.value)


def verified_sdk():
    sdk = import_module("cl")
    distribution = metadata.distribution("cl-sdk")
    expected = Path(distribution.locate_file("cl/__init__.py")).resolve()
    if distribution.version != "1.0.0" or Path(sdk.__file__).resolve() != expected:
        raise RuntimeError(SessionState.HARDWARE_UNQUALIFIED.value)
    require_simulator(sdk)
    return sdk


class SimulatorSession:
    def __init__(self, mapping=FIXTURE_MAP):
        if not set(mapping.stimulation) <= set(FIXTURE_MAP.allowed_stimulation):
            raise ValueError("Mapping outside qualified simulator fixture destinations")
        self.mapping = mapping
        self.state = SessionState.CLOSED
        self.pending = None
        self.last_observation_stop = None

    @contextmanager
    def open(self):
        if self.state is not SessionState.CLOSED:
            raise RuntimeError("Session cannot be opened")
        try:
            self.sdk = verified_sdk()
        except Exception:
            self.state = SessionState.HARDWARE_UNQUALIFIED
            raise
        with self.sdk.open() as self.neurons:
            if (
                self.neurons.get_frames_per_second() != FRAME_HZ
                or self.neurons.get_channel_count() != self.mapping.electrode_count
            ):
                raise RuntimeError("Incompatible SDK frame metadata")
            self.state = SessionState.OPEN_SIMULATOR
            try:
                yield self
            finally:
                self.state = SessionState.CLOSED
                self.pending = None
                self.last_observation_stop = None

    def submit(self, request, observation, clock):
        if self.state is not SessionState.OPEN_SIMULATOR:
            return StimDecision(request.request_id, False, self.state.value)
        try:
            require_simulator(self.sdk)
        except RuntimeError:
            self.state = SessionState.HARDWARE_UNQUALIFIED
            raise
        now = self.neurons.timestamp()
        try:
            electrode = validate_stim(request, observation, clock, self.mapping, now)
            if self.pending is not None or (
                self.last_observation_stop is not None
                and observation.stop <= self.last_observation_stop
            ):
                raise ValueError("Duplicate decision or outstanding command")
        except ValueError as error:
            return StimDecision(request.request_id, False, str(error))
        phases = tuple(value for phase in request.phases_us_uA for value in phase)
        self.neurons.stim(
            self.sdk.ChannelSet(electrode),
            self.sdk.StimDesign(*phases),
            lead_time_us=request.lead_us,
        )
        self.pending = (request, electrode, now)
        self.last_observation_stop = observation.stop
        return StimDecision(request.request_id, True, "submitted", electrode, now)

    def receipts(self, events, stop_frame):
        receipts = []
        for event in events:
            if self.pending is None:
                raise RuntimeError("Unsolicited committed stimulation")
            request, electrode, submitted = self.pending
            if (
                event.channel != electrode
                or not submitted <= event.timestamp < stop_frame
                or event.timestamp >= request.expires_frame
            ):
                raise RuntimeError("Commit does not match pending request")
            receipts.append(
                StimReceipt(request.request_id, request.clock, electrode, event.timestamp)
            )
            self.pending = None
        if self.pending is not None and stop_frame >= self.pending[0].expires_frame:
            raise RuntimeError("Missing committed stimulation by expiry")
        return receipts


class CountPI:
    """Receipt-gated binary pulse policy in spike-count units."""

    def __init__(self):
        self.integral = 0.0
        self.pending_error = None

    def propose(self, observation):
        if self.pending_error is not None:
            raise RuntimeError("Previous decision awaits confirmation")
        if not all(observation.valid) or observation.late:
            return False
        error = 2 - observation.counts[0]
        if error + 0.2 * self.integral > 0.5:
            self.pending_error = error
            return True
        self._advance(error)
        return False

    def resolve(self, committed):
        if self.pending_error is None:
            raise RuntimeError("No pending PI update")
        if committed:
            self._advance(self.pending_error)
        self.pending_error = None

    def _advance(self, error):
        self.integral = max(-2.0, min(2.0, self.integral + error))
