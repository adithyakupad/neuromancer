"""Causal M004 FIR updates and residual CUSUM; no simulator/gain/sham access."""

import numpy as np

FIT = slice(790, 1950)
NAMES = ("FROZEN", "SW250", "SW500", "RLS995", "RLS999", "SHUFFLED", "ARX")


def features(u, k, q=10):
    u = np.asarray(u, float)
    k = np.asarray(k, int)
    if u.ndim != 2 or u.shape[1] != 4 or k.ndim != 1 or k.min() < q - 1 or k.max() >= len(u):
        raise ValueError("Invalid causal delivered/planned input history")
    x = np.column_stack([u[k - j] for j in range(q)])
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite feature")
    return x


def ridge(z, target, lam=0.1):
    if (
        z.ndim != 2
        or target.shape != (len(z), 4)
        or not np.isfinite(z).all()
        or not np.isfinite(target).all()
    ):
        raise ValueError("Invalid regression rows")
    penalty = np.eye(z.shape[1]) * len(z) * lam
    penalty[0, 0] = 0
    a = z.T @ z + penalty
    h = z.T @ target
    theta = np.linalg.solve(a, h)
    if not np.isfinite(theta).all() or np.linalg.cond(a) > 1e12:
        raise ValueError("Invalid normal equations")
    return theta, np.linalg.inv(a)


def initialize(y, u, stop=1950, arx=False, shuffled=False):
    k = np.arange(790, stop)
    x = features(u, k, 4 if arx else 10)
    if arx:
        x = np.column_stack([*[y[k - j] for j in range(1, 5)], x])
    if shuffled:
        x = np.roll(x, 250, axis=0)
    if not np.isfinite(y[k]).all():
        raise ValueError("Incomplete calibration")
    mean = x.mean(axis=0)
    scale = np.maximum(x.std(axis=0), 1.0)
    ym = y[k].mean(axis=0)
    z = np.column_stack([np.ones(len(k)), (x - mean) / scale])
    theta, p = ridge(z, y[k] - ym)
    record = dict(
        coef=theta.tolist(),
        mean=mean.tolist(),
        scale=scale.tolist(),
        output_mean=ym.tolist(),
        diagnostics=dict(
            rank=int(np.linalg.matrix_rank(z)),
            features=x.shape[1],
            parameters=theta.size,
            condition=float(min(np.linalg.cond(z), 1e300)),
            information_condition=float(np.linalg.cond(np.linalg.inv(p))),
            rows=len(k),
        ),
    )
    if arx:
        beta = theta[1:] / scale[:, None]
        companion = np.zeros((16, 16))
        companion[:4] = np.column_stack([beta[4 * j : 4 * j + 4].T for j in range(4)])
        companion[4:, :-4] = np.eye(12)
        record["diagnostics"]["spectral_radius"] = float(max(abs(np.linalg.eigvals(companion))))
        if record["diagnostics"]["spectral_radius"] >= 0.999:
            raise ValueError("Unstable secondary ARX")
    return record, z, y[k] - ym, p


def standardized(record, x):
    return np.column_stack([np.ones(len(x)), (x - record["mean"]) / record["scale"]])


def checked(value):
    if not np.isfinite(value).all() or np.abs(value).max(initial=0) > 100:
        raise ValueError("Unbounded prediction; never clipped")
    return value


class OnlineFIR:
    """predict first; assimilate one completed bin afterward, with explicit skips."""

    def __init__(self, record, z, target, p, kind="FROZEN"):
        if kind not in NAMES[:-1]:
            raise ValueError("Unknown update method")
        self.record = record
        self.theta = np.array(record["coef"])
        self.p = p.copy()
        self.kind = kind
        self.z = list(z[-500:].copy())
        self.target = list(target[-500:].copy())
        self.time_us = 39_000_000
        self.received = 0
        self.updates = 0
        self.skips = 0
        self.refits = 0
        self.failed = False
        self.failures = []

    def forecast(self, x, origin_us):
        if origin_us != self.time_us:
            raise ValueError("Forecast origin is not the causal current clock")
        z = standardized(self.record, x)
        if not np.isfinite(z).all():
            raise ValueError("Invalid features")
        return checked(z @ self.theta + np.array(self.record["output_mean"]))

    def update(self, x, y, stop_us, available_us, valid=True):
        if stop_us != self.time_us + 20000 or available_us < stop_us:
            raise ValueError("Future, duplicate or out-of-order observation")
        self.time_us = stop_us
        self.received += 1
        if (
            not valid
            or available_us > stop_us
            or not np.isfinite(x).all()
            or not np.isfinite(y).all()
            or self.failed
        ):
            self.skips += 1
            return
        if self.kind in ("FROZEN", "SHUFFLED"):
            return
        z = standardized(self.record, np.asarray(x)[None])[0]
        v = np.asarray(y) - self.record["output_mean"]
        try:
            if self.kind.startswith("RLS"):
                rho = 0.995 if self.kind == "RLS995" else 0.999
                denom = rho + z @ self.p @ z
                if not np.isfinite(denom) or denom <= 0:
                    raise ValueError("Nonpositive RLS denominator")
                gain = self.p @ z / denom
                prediction_residual = v - z @ self.theta
                theta = self.theta + np.outer(gain, prediction_residual)
                p = (self.p - np.outer(gain, z @ self.p)) / rho
                p = (p + p.T) / 2
                if not np.isfinite(p).all() or not np.isfinite(theta).all():
                    raise ValueError("Nonfinite RLS state")
                if self.received == 1 or self.received % 50 == 0:
                    if np.linalg.eigvalsh(p).min() < -1e-8 or np.linalg.cond(p) > 1e12:
                        raise ValueError("Unstable RLS information")
                self.theta = theta
                self.p = p
                self.updates += 1
            else:
                self.z.append(z)
                self.target.append(v)
                self.z = self.z[-500:]
                self.target = self.target[-500:]
                self.updates += 1
                if self.received % 50 == 0:
                    window = int(self.kind[2:])
                    theta, _ = ridge(np.array(self.z[-window:]), np.array(self.target[-window:]))
                    self.theta = theta
                    self.refits += 1
        except (ValueError, np.linalg.LinAlgError) as e:
            self.failed = True
            self.failures.append(dict(stop_us=stop_us, reason=str(e)))


class ResidualCUSUM:
    def __init__(self, sigma, nu, threshold):
        if (
            not np.isfinite([sigma, nu, threshold]).all()
            or sigma < 0.1
            or nu not in (0.25, 0.5)
            or threshold not in (3, 5, 8, 12)
        ):
            raise ValueError("Unregistered detector")
        self.sigma = sigma
        self.nu = nu
        self.threshold = threshold
        self.value = 0.0
        self.time_us = 39_000_000
        self.last_alarm = -10_000_000

    def update(self, residual, mean_total_pA, stop_us):
        if stop_us != self.time_us + 1_000_000 or not np.isfinite([residual, mean_total_pA]).all():
            raise ValueError("Invalid completed detector block")
        self.time_us = stop_us
        armed = mean_total_pA >= 30
        if armed:
            self.value = max(0.0, self.value + residual / self.sigma - self.nu)
        before = self.value
        alarm = armed and self.value >= self.threshold and stop_us - self.last_alarm >= 5_000_000
        if alarm:
            self.last_alarm = stop_us
            self.value = 0.0
        return dict(stop_us=stop_us, statistic=before, armed=bool(armed), alarm=bool(alarm))
