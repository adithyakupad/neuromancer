"""M005A observation-only setpoint policies and general slew-aware projection.

No Brian objects, neural realization or efficacy parameter enter this module.
All public boundary times are integer microseconds, currents pA and rates Hz.
"""

from dataclasses import dataclass
import math
import numpy as np
from .calibration import fit as historical_calibration
from .observation import Observation
from .substrate import Command, Receipt

BIN_US = 20_000
GAINS = {"PI10_5": (10.0, 5.0), "PI20_10": (20.0, 10.0), "PI30_15": (30.0, 15.0)}


def project(request, previous):
    """Euclidean projection onto the box/slew/total-budget intersection.

    Invalid requests receive a labeled nearest-zero fallback. Invalid actuator
    state raises: it cannot be made retrospectively valid by this projector.
    """
    p = np.asarray(previous, dtype=float)
    if (
        p.shape != (4,)
        or not np.isfinite(p).all()
        or np.any(p < 0)
        or np.any(p > 120)
        or p.sum() > 240
    ):
        raise ValueError("Previous current is not feasible")
    low, high = np.maximum(0.0, p - 30), np.minimum(120.0, p + 30)
    # Round endpoints inward only when subtraction would violate the backend's
    # exact floating-point slew check. Never loosen the physical constraint.
    for _ in range(64):
        lower_bad = p - low > 30.0
        upper_bad = high - p > 30.0
        if not (lower_bad.any() or upper_bad.any()):
            break
        low[lower_bad] = np.nextafter(low[lower_bad], p[lower_bad])
        high[upper_bad] = np.nextafter(high[upper_bad], p[upper_bad])
    else:
        raise ArithmeticError("Cannot represent feasible slew endpoints")
    try:
        r = np.asarray(request, dtype=float)
        valid = r.shape == (4,) and np.isfinite(r).all()
    except (ValueError, TypeError):
        valid = False
    if not valid:
        return low, "invalid request: safe ramp"
    clipped = np.clip(r, low, high)
    if clipped.sum() <= 240:
        return clipped, "projected" if not np.array_equal(clipped, r) else "unchanged"
    lo, hi = 0.0, float(np.max(r - low))
    for _ in range(100):
        mid = (lo + hi) / 2
        if np.clip(r - mid, low, high).sum() > 240:
            lo = mid
        else:
            hi = mid
    result = np.clip(r - hi, low, high)
    # hi always brackets a feasible point, including floating-point equality.
    if result.sum() > 240:
        raise ArithmeticError("Projection failed its budget check")
    return result, "projected"


@dataclass(frozen=True, slots=True)
class ControlCalibration:
    baseline_hz: float
    noise_hz: float
    slope_hz_per_pA: float
    feedforward_pA: float
    target_hz: float
    h_hz: tuple[float, ...]
    valid: bool
    reason: str


def calibrate(observations, receipts):
    """Only completed original [0,47)s observations/receipts; no future data."""
    old = historical_calibration(tuple(observations), tuple(receipts))
    q = np.array([0.0, 30.0, 60.0, 90.0, 120.0])
    h = np.array(old.h_hz)
    slope = float(q @ h / (q @ q))
    ff = 1 / slope if slope > 0 else math.inf
    c = np.array([o.counts for o in observations[350:750]], float).reshape(400, 4, 5)
    seconds = c[:, :, :4].sum(axis=(1, 2)).reshape(8, 50).sum(axis=1) / 80.0
    noise = float(seconds.std(ddof=1))
    valid = bool(
        np.isfinite(h).all()
        and 1 <= old.baseline_hz <= 30
        and slope > 0
        and np.max(abs(q * slope - h)) <= 0.5
        and np.min(np.diff(h)) >= -0.3
        and 0 <= ff <= 120
    )
    return ControlCalibration(
        old.baseline_hz,
        noise,
        slope,
        ff if math.isfinite(ff) else 0.0,
        old.baseline_hz + 1.0,
        tuple(h),
        valid,
        "valid" if valid else "invalid dose calibration",
    )


class Policy:
    """One policy instance per independent controller trial.

    accept() receives only a completed permitted Observation and current time.
    desired() never sees an engine, true gain, or evaluator measurements.
    Late/missing input clears aggregation and freezes integral until rearmed.
    """

    __slots__ = (
        "calibration",
        "name",
        "kp",
        "ki",
        "aggregate_bins",
        "integral",
        "q",
        "expected_us",
        "samples",
        "recover",
        "safe",
        "last_status",
        "last_error",
        "blocked",
        "saturated",
        "updates",
        "trial_id",
    )

    def __init__(
        self,
        calibration: ControlCalibration,
        name: str,
        *,
        aggregate_bins: int = 50,
        start_us: int = 51_000_000,
    ):
        if name not in ("ZERO", "FIXED", "MAX", *GAINS):
            raise ValueError("Unknown fixed policy family")
        if type(aggregate_bins) is not int or aggregate_bins <= 0:
            raise ValueError("Positive integer observation aggregation required")
        self.calibration, self.name = calibration, name
        self.kp, self.ki = GAINS.get(name, (0.0, 0.0))
        self.aggregate_bins = aggregate_bins
        self.integral = 0.0
        if name == "ZERO":
            self.q = 0.0
        elif name == "MAX":
            self.q = 120.0
        else:
            self.q = calibration.feedforward_pA
        self.expected_us = start_us
        self.samples = []
        self.recover = 4
        self.safe = not calibration.valid and name not in ("ZERO", "MAX")
        self.last_status = "invalid calibration" if self.safe else "ready"
        self.last_error = math.nan
        self.blocked = False
        self.saturated = False
        self.updates = 0
        self.trial_id = None

    def desired(self):
        q = 0.0 if self.safe else self.q
        return np.array([q, 0.0, q, 0.0])

    def missing(self, now_us: int):
        if type(now_us) is not int or now_us != self.expected_us + BIN_US:
            raise ValueError("Missing-bin clock must advance exactly one tick")
        self.expected_us = now_us
        self.samples.clear()
        self.recover = 0
        self.safe = True
        self.last_status = "missing observation"

    def accept(self, observation: Observation, now_us: int):
        if type(now_us) is not int or now_us != self.expected_us + BIN_US:
            raise ValueError("Nonsequential observation clock")
        if observation.stop_us > now_us or observation.available_us > now_us:
            raise ValueError("Future observation is unavailable")
        if self.trial_id is None:
            self.trial_id = observation.trial_id
        elif observation.trial_id != self.trial_id:
            raise ValueError("Cross-trial observation")
        valid = (
            (observation.start_us, observation.stop_us, observation.available_us)
            == (self.expected_us, now_us, now_us)
            and len(observation.counts) == 20
            and observation.valid == (True,) * 20
            and observation.coverage_us == (BIN_US,) * 20
            and all(type(c) is int and c >= 0 for c in observation.counts)
        )
        if not valid:
            self.missing(now_us)
            self.last_status = "late or invalid observation"
            return
        self.expected_us = now_us
        if not self.calibration.valid and self.name not in ("ZERO", "MAX"):
            self.safe = True
            self.last_status = "invalid calibration"
            return
        if self.recover < 4:
            self.recover += 1
            if self.recover == 4:
                self.safe = False
                self.last_status = "rearmed"
            return
        self.safe = False
        counts = np.asarray(observation.counts).reshape(4, 5)[:, :4].sum()
        self.samples.append(float(counts) / 1.6)
        self.last_status = "holding"
        if len(self.samples) < self.aggregate_bins:
            return
        rate = sum(self.samples) / len(self.samples)
        self.samples.clear()
        self.last_error = self.calibration.target_hz - rate
        self.blocked = False
        self.saturated = False
        if self.name in GAINS:
            dt = self.aggregate_bins * 0.02
            # Integrate only a completed aggregation window; dt is in seconds.
            proposed_integral = float(
                np.clip(self.integral + self.ki * self.last_error * dt, -120.0, 120.0)
            )
            command = (
                self.calibration.feedforward_pA + self.kp * self.last_error + proposed_integral
            )
            self.blocked = bool(
                (command > 120 and self.last_error > 0) or (command < 0 and self.last_error < 0)
            )
            # Freeze integration when the error would push farther into saturation.
            if not self.blocked:
                self.integral = proposed_integral
            command = self.calibration.feedforward_pA + self.kp * self.last_error + self.integral
            self.q = float(np.clip(command, 0.0, 120.0))
            self.saturated = command != self.q
        if not np.isfinite([self.q, self.integral]).all():
            self.safe = True
            self.recover = 0
            self.last_status = "numerical failure"
            return
        self.updates += 1
        self.last_status = "updated"

    def record(self):
        return (
            self.expected_us,
            self.q,
            self.integral,
            self.last_error,
            float(self.blocked),
            float(self.saturated),
            float(self.safe),
            self.updates,
        )


def feedback_step(trial, policy: Policy, previous):
    """General20ms causal path, including missing/delayed-observation fallback.

    The just-completed observation can affect only the subsequent call's action.
    """
    if trial.time_us != policy.expected_us:
        raise ValueError("Controller and neural clocks disagree")
    current, status = project(policy.desired(), previous)
    start = trial.time_us
    command = Command(
        trial.metadata["trial_id"], f"feedback-{start}", start, tuple(map(float, current))
    )
    result = trial.advance(command, start + BIN_US)
    if result.receipt.delivered_current_pA != command.current_pA:
        raise RuntimeError("Unexpected delivered action")
    policy.accept(result.observation, trial.time_us)
    return result, status
