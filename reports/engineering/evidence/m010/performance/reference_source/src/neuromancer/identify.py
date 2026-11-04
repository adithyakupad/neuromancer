"""Observation-only M003 linear prediction. No simulator, gain or sham inputs."""

from dataclasses import dataclass
import numpy as np

FIT = slice(753, 2350)
HYPER_ORIGINS = range(2350, 2701, 10)
CAL_ORIGINS = range(2750, 3101, 10)
HORIZONS = (1, 10, 50)
GRID = tuple((p, lam) for p in (1, 4) for lam in (0.0001, 0.001, 0.01, 0.1))
FAMILIES = ("CONSTANT", "AR", "ARX", "SHUFFLED")


def arrays(y, u):
    y = np.asarray(y, dtype=float)
    u = np.asarray(u, dtype=float)
    if y.ndim != 2 or y.shape[1] != 4 or u.shape != y.shape:
        raise ValueError("Expected aligned Nx4 rates and currents")
    return y, u


def features(y, u, indices, p, inputs):
    indices = np.asarray(indices)
    if indices.ndim != 1 or indices.min() < max(p, 3 if inputs else p):
        raise ValueError("Insufficient causal history")
    x = np.concatenate([y[indices - lag] for lag in range(1, p + 1)], axis=1)
    if inputs:
        x = np.c_[x, *[u[indices - lag] for lag in range(4)]]
    if not np.isfinite(x).all():
        raise ValueError("Missing/nonfinite fitting features")
    return x


@dataclass
class Predictor:
    family: str
    p: int
    coef: np.ndarray
    mean: np.ndarray
    scale: np.ndarray
    output_mean: np.ndarray
    diagnostics: dict

    @property
    def inputs(self):
        return self.family in ("ARX", "SHUFFLED")

    def forecast(self, y_history, u_history, plan):
        """Forecast Nx4 rates (Hz) recursively from completed rates and known inputs."""
        plan = np.asarray(plan, dtype=float)
        if plan.ndim != 2 or plan.shape[1] != 4 or not np.isfinite(plan).all():
            raise ValueError("Invalid planned currents")
        if not self.diagnostics["valid"]:
            raise ValueError("Rejected predictor")
        if self.family == "CONSTANT":
            return np.tile(self.output_mean, (len(plan), 1))
        y, u = arrays(y_history, u_history)
        if len(y) < max(self.p, 3 if self.inputs else self.p):
            raise ValueError("Insufficient completed history")
        if not np.isfinite(y[-self.p :]).all() or (self.inputs and not np.isfinite(u[-3:]).all()):
            raise ValueError("Invalid completed history")
        rate_history = list(y[-max(self.p, 3) :].copy())
        current_history = list(u[-3:].copy())
        predictions = []
        for action in plan:
            feature_row = np.concatenate([rate_history[-lag] for lag in range(1, self.p + 1)])
            if self.inputs:
                feature_row = np.r_[
                    feature_row, action, *[current_history[-lag] for lag in range(1, 4)]
                ]
            predicted_rate = (
                self.output_mean + np.r_[1.0, (feature_row - self.mean) / self.scale] @ self.coef
            )
            if not np.isfinite(predicted_rate).all() or np.abs(predicted_rate).max() > 100:
                raise ValueError("Invalid unbounded forecast; never clipped")
            predictions.append(predicted_rate)
            rate_history.append(predicted_rate)
            current_history.append(action)
        return np.asarray(predictions).reshape(-1, 4)

    def record(self):
        return dict(
            family=self.family,
            p=self.p,
            coef=self.coef.tolist(),
            mean=self.mean.tolist(),
            scale=self.scale.tolist(),
            output_mean=self.output_mean.tolist(),
            diagnostics=self.diagnostics,
        )

    @classmethod
    def load(cls, record):
        result = cls(
            **{
                **record,
                **{
                    k: np.asarray(record[k], dtype=float)
                    for k in ("coef", "mean", "scale", "output_mean")
                },
            }
        )
        if (
            result.coef.shape != (len(result.mean) + 1, 4)
            or result.scale.shape != result.mean.shape
            or np.any(result.scale <= 0)
        ):
            raise ValueError("Invalid predictor serialization")
        if not all(
            np.isfinite(a).all()
            for a in (result.coef, result.mean, result.scale, result.output_mean)
        ):
            raise ValueError("Nonfinite predictor")
        return result


def fit(y, u, family, p=1, lam=0.001):
    y, u = arrays(y, u)
    indices = np.arange(FIT.start, FIT.stop)
    if len(y) < FIT.stop or not np.isfinite(y[FIT]).all():
        raise ValueError("Incomplete fitting period")
    output_mean = y[FIT].mean(axis=0)
    if family == "CONSTANT":
        return Predictor(
            family,
            0,
            np.zeros((1, 4)),
            np.empty(0),
            np.empty(0),
            output_mean,
            dict(valid=True, parameters=4),
        )
    if family not in FAMILIES or p not in (1, 4) or not np.isfinite(lam) or lam <= 0:
        raise ValueError("Invalid model specification")
    inputs = family in ("ARX", "SHUFFLED")
    current = u.copy()
    if family == "SHUFFLED":
        current[FIT] = np.roll(current[FIT], 500, axis=0)
    x = features(y, current, indices, p, inputs)
    mean = x.mean(axis=0)
    floors = np.r_[np.ones(4 * p), np.ones(16)] if inputs else np.ones(4 * p)
    scale = np.maximum(x.std(axis=0), floors)
    z = np.c_[np.ones(len(x)), (x - mean) / scale]
    s = np.linalg.svd(z, compute_uv=False)
    rank = int(np.linalg.matrix_rank(z))
    condition = float(s[0] / s[-1]) if s[-1] > 0 else 1e300
    penalty = np.diag(np.r_[0.0, np.full(z.shape[1] - 1, np.sqrt(lam))])
    augmented = np.vstack([z / np.sqrt(len(x)), penalty])
    target = np.vstack([(y[FIT] - output_mean) / np.sqrt(len(x)), np.zeros((z.shape[1], 4))])
    coef = np.linalg.lstsq(augmented, target, rcond=None)[0]
    companion = np.zeros((4 * p, 4 * p))
    companion[:4] = np.concatenate(
        [
            (coef[1 + 4 * l : 1 + 4 * (l + 1)] / scale[4 * l : 4 * (l + 1), None]).T
            for l in range(p)
        ],
        axis=1,
    )
    if p > 1:
        companion[4:, :-4] = np.eye(4 * (p - 1))
    radius = float(np.abs(np.linalg.eigvals(companion)).max())
    penalized = float(np.linalg.cond(augmented))
    valid = bool(
        rank == z.shape[1]
        and condition <= 1e6
        and penalized <= 1e8
        and radius < 0.999
        and np.isfinite(coef).all()
    )
    diagnostics = dict(
        valid=valid,
        parameters=int(coef.size),
        features=int(x.shape[1]),
        rank=rank,
        condition=condition,
        penalized_condition=penalized,
        spectral_radius=radius,
        singular_values=s.tolist(),
        lambda_value=lam,
        trained_start_us=15_000_000,
        trained_stop_us=47_000_000,
    )
    return Predictor(family, p, coef, mean, scale, output_mean, diagnostics)


def window_errors(model, y, u, origins, horizon=50):
    return np.array(
        [
            model.forecast(y[:k], u[:k], u[k : k + horizon]).mean(axis=0)
            - y[k : k + horizon].mean(axis=0)
            for k in origins
        ]
    )


def intervals(model, y, u):
    errors = [window_errors(model, y, u, CAL_ORIGINS, h) for h in HORIZONS]
    widths = np.array([np.quantile(np.abs(e), 0.95, axis=0, method="higher") for e in errors])
    threshold = float(np.quantile(errors[-1].mean(axis=1), 0.05, method="lower"))
    return widths, threshold


def bootstrap(values):
    values = np.asarray(values, dtype=float)
    if values.ndim < 1 or not np.isfinite(values).all():
        raise ValueError("Invalid network statistics")
    draws = np.random.default_rng(20261030).integers(0, len(values), (10000, len(values)))
    sampled = values[draws].mean(axis=1)
    return dict(
        mean=values.mean(axis=0).tolist(),
        lower=np.quantile(sampled, 0.025, axis=0).tolist(),
        upper=np.quantile(sampled, 0.975, axis=0).tolist(),
    )


def qualification(mse):
    """Nx4 network MSE, in CONSTANT,AR,ARX,SHUFFLED order; never bin replication."""
    mse = np.asarray(mse, dtype=float)
    if mse.ndim != 2 or mse.shape[1] != 4 or not np.isfinite(mse).all() or np.any(mse < 0):
        raise ValueError("Invalid network MSE")
    comparisons = {}
    required = 8 if len(mse) == 10 else 4
    for name, index in (("AR", 1), ("SHUFFLED", 3)):
        improvement = mse[:, index] - mse[:, 2]
        relative = improvement / np.maximum(mse[:, index], 0.04)
        absolute_ci = bootstrap(improvement)
        relative_ci = bootstrap(relative)
        comparisons[name] = dict(
            absolute=absolute_ci,
            relative=relative_ci,
            floor_count=int((mse[:, index] < 0.04).sum()),
            positive_networks=int((improvement > 0).sum()),
            passed=bool(
                absolute_ci["mean"] >= 0.04
                and relative_ci["mean"] >= 0.10
                and absolute_ci["lower"] > 0
                and (improvement > 0).sum() >= required
            ),
        )
    return dict(
        scientific_gate="PASS" if all(c["passed"] for c in comparisons.values()) else "FAIL",
        comparisons=comparisons,
    )
