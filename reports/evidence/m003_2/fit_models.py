"""Fit26/27, select/calibrate28, forecast29/30/31 without opening their outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.calibration_diagnostic import save_json
from neuromancer.state_dependence import FAMILIES, LAMBDAS, matrix, solve, effect, arx_matrix, arx_forecast
from neuromancer.state_experiment import NAMES

STRATA = ('LOW', 'HIGH')
HORIZONS = (1, 10, 50, 100)


def load_origins(raw, n, rep, outcomes=False):
    trial = raw/f'n{n}_r{rep}'
    with np.load(trial/'plans.npz') as f: plan = f['planned'].copy()
    result = []
    for stratum in STRATA:
        with np.load(trial/stratum/'origin.npz') as f: origin = {k: f[k].copy() for k in f.files}
        origin['stratum'] = stratum; origin['plan'] = plan
        if outcomes:
            origin['y'] = np.array([np.load(trial/stratum/f'{name}.npz')['rates'] for name in NAMES])
        result.append(origin)
    return result


def training(raw, n, reps, family):
    origins = [o for rep in reps for o in load_origins(raw, n, rep, True)]
    values = np.array([float(o['rate']) for o in origins]); mean = float(values.mean()); sd = max(float(values.std()), .1)
    xs = []; ys = []
    for i, o in enumerate(origins):
        a = float(origins[i ^ 1]['rate']) if family == 'STATE_SHUFFLED' else float(o['rate'])
        if family == 'ARX':
            for j in range(7):
                xs.append(arx_matrix(o['history'], o['y'][j], o['plan'][j])); ys.append(o['y'][j])
        else:
            for j in range(1, 7):
                x = matrix(o['plan'][j], a, mean, sd, family)
                if family == 'FIR_SHUFFLED': x = np.roll(x, 25, axis=0)
                xs.append(x); ys.append(o['y'][j]-o['y'][0])
    return np.vstack(xs), np.vstack(ys), mean, sd


def fitted(x, y, mean, sd, family, lam):
    record = solve(x, y, lam, intercept=family == 'ARX'); record.update(family=family, state_mean=mean, state_sd=sd)
    if family == 'ARX':
        beta = np.array(record['coef'])[1:]/np.array(record['scale'])[:, None]
        companion = np.zeros((16, 16)); companion[:4] = np.column_stack([beta[4*j:4*j+4].T for j in range(4)])
        companion[4:, :-4] = np.eye(12)
        radius = float(np.max(np.abs(np.linalg.eigvals(companion)))); record['diagnostics']['radius'] = radius
        if radius >= .999: raise ValueError('Unstable ARX')
    return record


def predict(record, origin):
    if record['family'] == 'ARX':
        absolute = np.array([arx_forecast(record, origin['history'], u) for u in origin['plan']])
        return absolute-absolute[0], absolute
    delta = np.array([effect(record, u, float(origin['rate'])) for u in origin['plan']])
    return delta, delta+origin['history'][-1]


def loss(record, origins):
    values = []
    for o in origins:
        delta, absolute = predict(record, o)
        predicted, actual = (absolute, o['y']) if record['family'] == 'ARX' else (delta[1:], (o['y']-o['y'][0])[1:])
        values.append(float(np.mean((predicted[:, :50].mean(axis=1)-actual[:, :50].mean(axis=1))**2)))
    return float(np.mean(values))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--raw', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False); began = time.perf_counter()
    from neuromancer.diagnostic import provenance
    source = provenance()
    source['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    source['protocol_sha256'] = hashlib.sha256(Path('docs/research/007_M003_2_STATE_DEPENDENCE_PROTOCOL.md').read_bytes()).hexdigest()
    source['evaluated_split'] = 'fit26/27, selection28; forecast origins/plans only29/30 and null31, networks0-9'
    save_json(args.output/'provenance.json', source)
    candidates = {}; scores = {family: [] for family in FAMILIES}
    for n in range(10):
        validation = load_origins(args.raw, n, 28, True)
        for family in FAMILIES:
            x, y, mean, sd = training(args.raw, n, (26, 27), family)
            for lam in LAMBDAS:
                record = fitted(x, y, mean, sd, family, lam)
                score = loss(record, validation); key = f'n{n}_{family}_{lam}'
                candidates[key] = dict(model=record, validation_mse=score)
        print('fit', n, flush=True)
    for family in FAMILIES:
        for lam in LAMBDAS:
            scores[family].append(dict(lam=lam, mse=float(np.mean([candidates[f'n{n}_{family}_{lam}']['validation_mse'] for n in range(10)]))))
    chosen = {}
    for family, rows in scores.items():
        best = min(r['mse'] for r in rows)
        chosen[family] = max(r['lam'] for r in rows if r['mse'] <= best+1e-12)
    save_json(args.output/'candidates.json', candidates); save_json(args.output/'selection.json', dict(chosen=chosen, scores=scores))
    models = {}; half = {}; widths = np.zeros((10, 5, 4))
    for n in range(10):
        validation = load_origins(args.raw, n, 28, True)
        for m, family in enumerate(FAMILIES):
            record = candidates[f'n{n}_{family}_{chosen[family]}']['model']; models[f'n{n}_{family}'] = record
            x, y, mean, sd = training(args.raw, n, (26,), family)
            half[f'n{n}_{family}'] = fitted(x, y, mean, sd, family, chosen[family])
            errors = [[] for _ in HORIZONS]
            for o in validation:
                delta, _ = predict(record, o); actual = o['y']-o['y'][0]
                for h, size in enumerate(HORIZONS):
                    errors[h].extend(np.abs(delta[1:, :size].mean(axis=1)-actual[1:, :size].mean(axis=1)).ravel())
            for h in range(4): widths[n, m, h] = np.quantile(errors[h], .95, method='higher')
    save_json(args.output/'selected.json', models); save_json(args.output/'half_selected.json', half)
    np.savez_compressed(args.output/'intervals.npz', widths=widths)
    # Only origin.npz and plans.npz are opened below, never reserved branch files.
    for n in range(10):
        for rep in ((29, 30, 31) if n < 3 else (29, 30)):
            origins = load_origins(args.raw, n, rep, False)
            for suffix, records in (('', models), ('_half', half)):
                delta = np.empty((5, 2, 7, 100, 4)); absolute = np.empty_like(delta)
                for m, family in enumerate(FAMILIES):
                    for s, o in enumerate(origins): delta[m, s], absolute[m, s] = predict(records[f'n{n}_{family}'], o)
                np.savez_compressed(args.output/f'n{n}_r{rep}{suffix}.npz', delta=delta, absolute=absolute)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.iterdir() if p.is_file()}
    save_json(args.output/'forecast_seal.json', dict(artifact_sha256=hashes, wall_s=time.perf_counter()-began,
              accesses='Fit26/27, validation28 outcomes; reserved29/30/null31 origin histories and input plans only'))


if __name__ == '__main__': main()
