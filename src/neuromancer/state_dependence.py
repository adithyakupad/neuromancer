"""M003.2 fixed-origin bilinear FIR; no simulator or future observations."""
import numpy as np

LAMBDAS = (.0001, .001, .01, .1)
FAMILIES = ('FIR', 'STATE', 'STATE_SHUFFLED', 'FIR_SHUFFLED', 'ARX')


def origin_rate(completed):
    y = np.asarray(completed, dtype=float)
    if y.ndim != 2 or y.shape[1] != 4 or len(y) < 5 or not np.isfinite(y[-5:]).all():
        raise ValueError('Five finite completed four-sector observations required')
    return float(y[-5:].mean())


def thresholds(calibration):
    y = np.asarray(calibration, dtype=float)
    if y.shape != (500, 4) or not np.isfinite(y).all():
        raise ValueError('Exactly 500 completed calibration observations required')
    values = np.array([origin_rate(y[:k]) for k in range(5, 501)])
    lo, hi = np.quantile(values, [.25, .75], method='linear')
    if not lo < hi:
        raise ValueError('Degenerate origin calibration')
    return [float(lo), float(hi)]


def label(completed, bounds):
    a = origin_rate(completed)
    if not np.isfinite(bounds).all() or not bounds[0] < bounds[1]:
        raise ValueError('Invalid calibration bounds')
    return 'LOW' if a <= bounds[0] else 'HIGH' if a >= bounds[1] else None


def inputs(plan):
    u = np.asarray(plan, dtype=float)
    if u.ndim != 2 or u.shape[1] != 4 or not np.isfinite(u).all():
        raise ValueError('Finite Nx4 delivered/known planned input required')
    past = np.vstack([np.zeros((9, 4)), u])
    return np.concatenate([past[9-j:9-j+len(u)] for j in range(10)], axis=1)


def matrix(plan, a, mean, sd, family):
    x = inputs(plan)
    if family.startswith('STATE'):
        if not np.isfinite(a) or not np.isfinite([mean, sd]).all() or sd < .1:
            raise ValueError('Finite causal origin scalar and fitted normalization required')
        x = np.column_stack([x, x * ((a-mean)/sd)])
    return x


def solve(x, y, lam, *, intercept=False):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.ndim != 2 or y.shape != (len(x), 4) or not np.isfinite(x).all() or not np.isfinite(y).all() or lam not in LAMBDAS:
        raise ValueError('Invalid finite ridge data or registered penalty')
    mean = x.mean(axis=0) if intercept else np.zeros(x.shape[1])
    scale = np.maximum(np.sqrt(((x-mean)**2).mean(axis=0)), 1.)
    z = (x-mean)/scale
    ym = y.mean(axis=0) if intercept else np.zeros(4)
    if intercept:
        z = np.column_stack([np.ones(len(z)), z])
    penalty = np.eye(z.shape[1])*np.sqrt(len(z)*lam)
    if intercept: penalty[0, 0] = 0
    aug = np.vstack([z, penalty])
    coef = np.linalg.lstsq(aug, np.vstack([y-ym, np.zeros((len(penalty), 4))]), rcond=None)[0]
    s = np.linalg.svd(z, compute_uv=False); sa = np.linalg.svd(aug, compute_uv=False)
    cond = float(sa[0]/sa[-1])
    if not np.isfinite(coef).all() or cond > 1e8:
        raise ValueError('Invalid penalized estimate')
    return dict(coef=coef.tolist(), mean=mean.tolist(), scale=scale.tolist(), output_mean=ym.tolist(),
                intercept=intercept, lam=lam, diagnostics=dict(features=x.shape[1], parameters=coef.size,
                rank=int(np.linalg.matrix_rank(z)), singular_values=s.tolist(),
                condition=float(s[0]/max(s[-1], np.finfo(float).tiny)), augmented_condition=cond))


def predict_matrix(record, x):
    z = (x-np.array(record['mean']))/np.array(record['scale'])
    if record['intercept']: z = np.column_stack([np.ones(len(z)), z])
    result = z @ np.array(record['coef']) + np.array(record['output_mean'])
    if not np.isfinite(result).all() or np.max(np.abs(result)) > 100:
        raise ValueError('Invalid forecast; no clipping')
    return result


def effect(record, plan, a=None):
    """Input-only FIR has no observation argument; STATE consumes one past scalar."""
    return predict_matrix(record, matrix(plan, a, record['state_mean'], record['state_sd'], record['family']))


def arx_matrix(history, y, plan):
    y = np.asarray(y); u = np.asarray(plan)
    pasty = np.vstack([history, y]); pastu = np.vstack([np.zeros((4, 4)), u])
    h = len(history)
    return np.column_stack([*[pasty[h-j:h-j+len(y)] for j in range(1, 5)],
                            *[pastu[4-j:4-j+len(y)] for j in range(4)]])


def arx_forecast(record, history, plan):
    yh = list(np.asarray(history)[-4:]); uh = list(np.zeros((3, 4))); result = []
    for u in plan:
        x = np.concatenate([*yh[::-1], u, *uh[::-1]])[None, :]
        value = predict_matrix(record, x)[0]; result.append(value); yh = yh[1:]+[value]; uh = uh[1:]+[u]
    return np.array(result)


def gate(fir, state, shuffled):
    f, s, c = map(lambda a: np.asarray(a, float), (fir, state, shuffled))
    if f.shape != (10,) or s.shape != f.shape or c.shape != f.shape or not np.isfinite([f, s, c]).all():
        raise ValueError('Ten paired finite network scores required')
    delta = f-s; relative = delta/np.maximum(f, .04)
    draws = np.random.default_rng(20261102).integers(0, 10, (10000, 10))
    interval = lambda x: np.quantile(x[draws].mean(axis=1), [.025, .975]).tolist()
    ci = interval(delta); control_ci = interval(c-s)
    magnitude = delta.mean() >= .04 and relative.mean() >= .1 and (delta > 0).sum() >= 8
    passed = magnitude and ci[0] > 0 and control_ci[0] > 0
    return dict(decision='PASS' if passed else 'HOLD' if magnitude else 'FAIL',
                absolute_improvement=float(delta.mean()), relative_improvement=float(relative.mean()),
                absolute_ci=ci, relative_ci=interval(relative), shuffled_improvement_ci=control_ci,
                positive_networks=int((delta > 0).sum()), denominator_floors=int((f < .04).sum()))
