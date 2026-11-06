"""Public-record-only FIR initialization, transactional adaptation and control.

No neural engine, physical gain or evaluator measurements enter these APIs.
Physical units: pA, Hz, integer microseconds; monotonic ns for wall budgets.
"""

from dataclasses import dataclass
import copy
import numpy as np
from .clocks import now_ns
from .control import calibrate, project, BIN_US
from .online_identify import features, ridge
from .predictive_planner import plan
from .substrate import Command, Receipt
from .observation import Observation


def initialize_raw(y, u):
    y = np.asarray(y, float)
    u = np.asarray(u, float)
    if y.shape != u.shape or y.shape != (2550, 4):
        raise ValueError("Complete raw51s prefix required")
    if not np.isfinite(y).all() or not np.isfinite(u).all():
        raise ValueError("Nonfinite prefix")
    if np.any(u[:, 1::2] != 0) or np.any(u[:, 0] != u[:, 2]):
        raise ValueError("C02 only")
    k = np.arange(800, 2350)
    x = features(u, k)
    mu = x.mean(0)
    scale = np.maximum(x.std(0), 1.0)
    ym = y[k].mean(0)
    z = np.c_[np.ones(len(x)), (x - mu) / scale]
    v = y[k] - ym
    reduced = np.c_[np.ones(len(k)), *[u[k - j, 0] for j in range(10)]]
    reduced[:, 1:] = (reduced[:, 1:] - reduced[:, 1:].mean(0)) / np.maximum(
        reduced[:, 1:].std(0), 1.0
    )
    rank = int(np.linalg.matrix_rank(reduced))
    condition = float(np.linalg.cond(reduced))
    if rank != 11 or condition > 1e6:
        raise ValueError("Unidentified C02 history")
    theta, p = ridge(z, v, 0.1)
    record = dict(
        coef=theta.tolist(),
        mean=mu.tolist(),
        scale=scale.tolist(),
        output_mean=ym.tolist(),
        diagnostics=dict(
            rank=int(np.linalg.matrix_rank(z)),
            reduced_rank=rank,
            reduced_condition=condition,
            information_condition=float(np.linalg.cond(np.linalg.inv(p))),
            parameters=theta.size,
            rows=len(z),
            singular_values=np.linalg.svd(z, compute_uv=False).tolist(),
            reduced_singular_values=np.linalg.svd(reduced, compute_uv=False).tolist(),
            fit_rows=[800, 2350],
        ),
    )
    return record, z, v, p


@dataclass(frozen=True)
class Initialization:
    record: dict
    information_inverse: np.ndarray
    history: np.ndarray
    calibration: object
    trial_id: str


def raw_observation(o: Observation, start: int, trial_id: str):
    if (
        not isinstance(o, Observation)
        or any(type(t) is not int for t in (o.start_us, o.stop_us, o.available_us))
        or (o.trial_id, o.start_us, o.stop_us, o.available_us)
        != (trial_id, start, start + BIN_US, start + BIN_US)
    ):
        raise ValueError("Unavailable/misaligned observation")
    if (
        o.valid != (True,) * 20
        or o.coverage_us != (BIN_US,) * 20
        or len(o.counts) != 20
        or any(type(v) is not int or v < 0 for v in o.counts)
    ):
        raise ValueError("Invalid observation channels/counts")
    return np.asarray(o.counts).reshape(4, 5)[:, :4].sum(axis=1) / 0.4


def initialize(observations, receipts) -> Initialization:
    if len(observations) != 2550 or len(receipts) != 2550:
        raise ValueError("Complete original51s prefix required")
    from .calibration import prefix_schedule

    trial = observations[0].trial_id
    ys = []
    us = []
    for k, (o, r) in enumerate(zip(observations, receipts, strict=True)):
        t = k * BIN_US
        ys.append(raw_observation(o, t, trial))
        if not isinstance(r, Receipt) or (
            r.trial_id,
            r.requested_start_us,
            r.delivered_start_us,
            r.delivered_stop_us,
        ) != (trial, t, t, t + BIN_US):
            raise ValueError("Invalid prefix receipt")
        us.append(r.delivered_current_pA)
    us = np.asarray(us, float)
    if not np.array_equal(us, prefix_schedule()):
        raise ValueError("Different calibration stimulation")
    record, z, v, p = initialize_raw(np.array(ys), us)
    if np.linalg.eigvalsh(p).min() <= 0:
        raise ValueError("Invalid initial information")
    return Initialization(
        record, p, us[-9:].copy(), calibrate(observations[:2350], receipts[:2350]), trial
    )


class FIRModel:
    """One independent model; timestamp ownership belongs to its controller."""

    def __init__(self, record, p, kind="FIXED"):
        if kind not in ("FIXED", "RLS", "BIAS"):
            raise ValueError("Unknown adaptation policy")
        self.record = copy.deepcopy(record)
        self.theta = np.array(record["coef"], float).copy()
        self.p = np.array(p, float).copy()
        self.kind = kind
        self.bias_p = 1.0 / record["diagnostics"]["rows"]
        self.received = 0
        self.updates = 0
        self.skips = 0
        self.failure = None
        if (
            self.theta.shape != (41, 4)
            or self.p.shape != (41, 41)
            or not np.isfinite(self.theta).all()
            or not np.isfinite(self.p).all()
        ):
            raise ValueError("Invalid model initialization")

    def standardized(self, x):
        x = np.asarray(x, float)
        if x.shape != (40,) or not np.isfinite(x).all():
            raise ValueError("Invalid features")
        return np.r_[1.0, (x - np.array(self.record["mean"])) / self.record["scale"]]

    def predict(self, x):
        y = np.array(self.record["output_mean"]) + self.standardized(x) @ self.theta
        if not np.isfinite(y).all() or abs(y).max() > 100:
            raise ValueError("Invalid prediction")
        return y

    def update(self, x, y, valid=True):
        self.received += 1
        if not valid or self.failure is not None:
            self.skips += 1
            return
        if self.kind == "FIXED":
            return
        try:
            z = self.standardized(x)
            v = np.asarray(y, float) - self.record["output_mean"]
            if v.shape != (4,) or not np.isfinite(v).all():
                raise ValueError("Invalid completed rate")
            if self.kind == "RLS":
                denominator = 0.999 + z @ self.p @ z
                if not np.isfinite(denominator) or denominator <= 0:
                    raise ValueError("Nonpositive denominator")
                gain = self.p @ z / denominator
                prediction_residual = v - z @ self.theta
                theta = self.theta + np.outer(gain, prediction_residual)
                p = (self.p - np.outer(gain, z @ self.p)) / 0.999
                p = (p + p.T) / 2
                if not np.isfinite(theta).all() or not np.isfinite(p).all():
                    raise ValueError("Nonfinite information")
                if self.received == 1 or self.received % 50 == 0:
                    if np.linalg.eigvalsh(p).min() < -1e-8 or np.linalg.cond(p) > 1e12:
                        raise ValueError("Unstable information")
                bias_p = self.bias_p
            else:
                denominator = 0.999 + self.bias_p
                gain = self.bias_p / denominator
                theta = self.theta.copy()
                theta[0] += gain * (v - z @ theta)
                bias_p = self.bias_p / denominator
                p = self.p
                if not np.isfinite(theta).all() or not np.isfinite(bias_p) or bias_p <= 0:
                    raise ValueError("Invalid intercept information")
            if (
                not np.isfinite(z @ theta).all()
                or abs(z @ theta + np.array(self.record["output_mean"])).max() > 100
            ):
                raise ValueError("Unbounded updated prediction")
            self.theta = theta
            self.p = p
            self.bias_p = bias_p
            self.updates += 1
        except (ValueError, np.linalg.LinAlgError, FloatingPointError) as e:
            self.failure = str(e)


class PredictiveController:
    """One trial, public receipts only; command BEFORE accept, never retroactive."""

    def __init__(self, initial: Initialization, kind="FIXED", *, clock=now_ns):
        self.model = FIRModel(initial.record, initial.information_inverse, kind)
        self.history = initial.history.copy()
        self.calibration = initial.calibration
        self.trial_id = initial.trial_id
        self.time_us = 51_000_000
        self.clock = clock
        self.pending = None
        self.q = 0.0
        self.safe = False
        self.recover = 4
        self.failure = None
        self.plans = []
        self.events = []
        self.last_prediction = None
        self.command_ns = []
        self.update_ns = []
        if not self.calibration.valid:
            self._fail("Invalid original calibration")

    def _fail(self, reason):
        if self.failure is None:
            self.failure = str(reason)
        self.safe = True
        self.q = 0.0

    def command(self, now_us: int) -> Command:
        if type(now_us) is not int or now_us != self.time_us or self.pending is not None:
            raise ValueError("Noncausal/duplicate command")
        began = self.clock()
        decision = (now_us - 51_000_000) % 1_000_000 == 0
        planning_start = None
        if decision and self.failure is None and self.recover == 4:
            planning_start = self.clock()
            try:
                result = plan(
                    self.model.record,
                    self.model.theta,
                    self.history,
                    self.calibration.target_hz,
                    now_us,
                    clock=self.clock,
                )
                self.q = result["q0"]
                self.safe = False
                result.update(theta=self.model.theta.copy(), history=self.history.copy())
                self.plans.append(result)
            except (ValueError, TimeoutError, ArithmeticError, np.linalg.LinAlgError) as e:
                self._fail(e)
        requested = np.array([self.q, 0.0, self.q, 0.0]) if not self.safe else np.zeros(4)
        current, status = project(requested, self.history[-1])
        x = np.r_[current, self.history[::-1].ravel()]
        try:
            self.last_prediction = self.model.predict(x)
        except ValueError as e:
            self._fail(e)
            current, status = project(np.zeros(4), self.history[-1])
            x = np.r_[current, self.history[::-1].ravel()]
            self.last_prediction = None
        # Deadline includes result validation and first legal release.
        if planning_start is not None and self.clock() - planning_start >= 250_000_000:
            self._fail("Complete planner release deadline exceeded")
            current, status = project(np.zeros(4), self.history[-1])
            x = np.r_[current, self.history[::-1].ravel()]
            self.last_prediction = None
        c = Command(self.trial_id, f"predictive-{now_us}", now_us, tuple(map(float, current)))
        self.pending = (c, x, self.last_prediction)
        self.command_ns.append(self.clock() - began)
        return c

    def accept(self, observation: Observation | None, receipt: Receipt, now_us: int):
        if self.pending is None or type(now_us) is not int or now_us != self.time_us + BIN_US:
            raise ValueError("Nonsequential completion")
        c, x, prediction = self.pending
        if (
            not isinstance(receipt, Receipt)
            or receipt.status != "delivered"
            or any(
                type(t) is not int
                for t in (
                    receipt.requested_start_us,
                    receipt.delivered_start_us,
                    receipt.delivered_stop_us,
                )
            )
            or type(receipt.delivered_current_pA) is not tuple
            or type(receipt.requested_current_pA) is not tuple
            or (
                receipt.trial_id,
                receipt.command_id,
                receipt.requested_start_us,
                receipt.delivered_start_us,
                receipt.delivered_stop_us,
            )
            != (self.trial_id, c.command_id, c.start_us, c.start_us, now_us)
            or receipt.delivered_current_pA != c.current_pA
            or receipt.requested_current_pA != c.current_pA
        ):
            self._fail("Invalid/unknown delivery receipt")
            raise ValueError("Invalid receipt; cannot advance known input history")
        began = self.clock()
        valid = True
        y = None
        try:
            y = raw_observation(observation, self.time_us, self.trial_id)
        except (ValueError, AttributeError, TypeError):
            valid = False
        if not valid:
            self.safe = True
            self.q = 0.0
            self.recover = 0
        elif self.recover < 4:
            self.recover += 1
            valid = False  # Rearm uses four bins, no retroactive update.
        self.model.update(x, y, valid and self.failure is None)
        if self.model.failure is not None:
            self._fail(self.model.failure)
        self.history = np.vstack([self.history[1:], receipt.delivered_current_pA])
        self.time_us = now_us
        self.pending = None
        self.events.append(
            dict(
                stop_us=now_us,
                valid_update=bool(valid and self.failure is None),
                safe=self.safe,
                recover=self.recover,
                failure=self.failure,
                received=self.model.received,
                updates=self.model.updates,
                skips=self.model.skips,
            )
        )
        self.update_ns.append(self.clock() - began)


def public_step(trial, controller):
    """Thin adapter; trial exposes only time_us and advance, never private state."""
    c = controller.command(trial.time_us)
    result = trial.advance(c, c.start_us + BIN_US)
    controller.accept(result.observation, result.receipt, result.observation.stop_us)
    return result


class PIReference:
    """Receipt-validating adapter around the unchanged historical PI Policy."""

    def __init__(self, calibration, trial_id, previous):
        from .control import Policy

        self.policy = Policy(calibration, "PI10_5")
        self.trial_id = trial_id
        self.previous = np.asarray(previous, float).copy()
        self.pending = None

    def command(self, now_us):
        if now_us != self.policy.expected_us or self.pending is not None:
            raise ValueError("Noncausal PI command")
        u, _ = project(self.policy.desired(), self.previous)
        c = Command(self.trial_id, f"pi-{now_us}", now_us, tuple(map(float, u)))
        self.pending = c
        return c

    def accept(self, observation, receipt, now_us):
        c = self.pending
        if (
            c is None
            or not isinstance(receipt, Receipt)
            or receipt.status != "delivered"
            or any(
                type(t) is not int
                for t in (
                    receipt.requested_start_us,
                    receipt.delivered_start_us,
                    receipt.delivered_stop_us,
                )
            )
            or receipt.requested_start_us != c.start_us
            or receipt.requested_current_pA != c.current_pA
            or (
                receipt.trial_id,
                receipt.command_id,
                receipt.delivered_start_us,
                receipt.delivered_stop_us,
                receipt.delivered_current_pA,
            )
            != (self.trial_id, c.command_id, c.start_us, now_us, c.current_pA)
        ):
            raise ValueError("Invalid PI receipt")
        if observation is None:
            self.policy.missing(now_us)
        else:
            self.policy.accept(observation, now_us)
        self.previous = np.array(receipt.delivered_current_pA)
        self.pending = None
