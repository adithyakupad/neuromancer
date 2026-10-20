"""Independent M003.2 equations; does not import study fitting/scoring routines."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np

FAMILIES = ('FIR', 'STATE', 'STATE_SHUFFLED', 'FIR_SHUFFLED', 'ARX')
NAMES = ('S', 'C0', 'C1', 'C2', 'C3', 'P', 'R')
LAMBDAS = (.0001, .001, .01, .1)


def read(path):
    with np.load(path, allow_pickle=False) as f: return {k: f[k].copy() for k in f.files}


def lags(u):
    x = np.zeros((len(u), 40))
    for j in range(10):
        if j < len(u): x[j:, 4*j:4*j+4] = u[:len(u)-j]
    return x


def check_observations(d, initial=None):
    counts = d['counts']; sector = counts.reshape(-1, 4, 5)[:, :, :4].sum(axis=2)/.4
    np.testing.assert_array_equal(sector, d['sector'])
    assert d['valid'].all() and (d['coverage_us'] == 20000).all()
    np.testing.assert_array_equal(d['requested'], d['delivered'])
    times = d['time_us']; assert (np.diff(times[:, 0]) == 20000).all()
    assert (times[:, 1] == times[:, 0]+20000).all() and (times[:, 2] == times[:, 1]).all()
    event_time = d['event_time_us']; channel = d['event_channel']; offset = d['event_offset']
    np.testing.assert_array_equal(offset, np.searchsorted(event_time, np.r_[times[:, 0], times[-1, 1]]))
    bins = (event_time-times[0, 0])//20000
    counted = np.bincount(bins*20+channel, minlength=len(counts)*20).reshape(-1, 20)
    np.testing.assert_array_equal(counted, counts)
    filtered = np.full_like(sector, np.nan); alpha = float(np.exp(-.2))
    if initial is None:
        state = counts[350:750].reshape(400, 4, 5)[:, :, :4].sum(axis=(0, 2))/160
        filtered[749] = state; start = 750
    else: state = np.array(initial); start = 0
    for k in range(start, len(counts)):
        state = alpha*state+(1-alpha)*sector[k]; filtered[k] = state
    np.testing.assert_allclose(filtered, d['rates'], rtol=0, atol=1e-12, equal_nan=True)


def origin(raw, n, rep, stratum): return read(raw/f'n{n}_r{rep}'/stratum/'origin.npz')


def training(raw, n, reps, family):
    origins = [(rep, s, origin(raw, n, rep, s)) for rep in reps for s in ('LOW', 'HIGH')]
    vals = np.array([float(o['rate']) for _, _, o in origins]); mean = vals.mean(); sd = max(vals.std(), .1)
    xs = []; ys = []
    for index, (rep, s, o) in enumerate(origins):
        plan = read(raw/f'n{n}_r{rep}'/'plans.npz')['planned']
        y = np.array([read(raw/f'n{n}_r{rep}'/s/f'{name}.npz')['rates'] for name in NAMES])
        if family == 'ARX':
            for a in range(7):
                past = np.vstack([o['history'], y[a]]); pastu = np.vstack([np.zeros((4, 4)), plan[a]])
                x = np.empty((100, 32))
                for k in range(100): x[k] = np.r_[np.concatenate([past[50+k-j] for j in range(1, 5)]), np.concatenate([pastu[4+k-j] for j in range(4)])]
                xs.append(x); ys.append(y[a])
        else:
            z = ((vals[index ^ 1] if family == 'STATE_SHUFFLED' else vals[index])-mean)/sd
            for a in range(1, 7):
                x = lags(plan[a])
                if family.startswith('STATE'): x = np.c_[x, z*x]
                if family == 'FIR_SHUFFLED': x = np.roll(x, 25, axis=0)
                xs.append(x); ys.append(y[a]-y[0])
    return np.vstack(xs), np.vstack(ys), float(mean), float(sd)


def estimate(x, y, record):
    intercept = record['intercept']; mean = x.mean(axis=0) if intercept else np.zeros(x.shape[1])
    scale = np.maximum(np.sqrt(np.mean((x-mean)**2, axis=0)), 1.)
    ym = y.mean(axis=0) if intercept else np.zeros(4)
    z = (x-mean)/scale
    if intercept: z = np.c_[np.ones(len(z)), z]
    penalty = np.eye(z.shape[1])*len(z)*record['lam']
    if intercept: penalty[0, 0] = 0
    coefficient = np.linalg.solve(z.T@z+penalty, z.T@(y-ym))
    np.testing.assert_allclose(record['mean'], mean, rtol=0, atol=1e-12)
    np.testing.assert_allclose(record['scale'], scale, rtol=0, atol=1e-12)
    np.testing.assert_allclose(record['output_mean'], ym, rtol=0, atol=1e-12)
    np.testing.assert_allclose(record['coef'], coefficient, rtol=1e-8, atol=1e-9)


def forecast(record, o, plan):
    coef = np.array(record['coef']); mean = np.array(record['mean']); scale = np.array(record['scale']); ym = np.array(record['output_mean'])
    def linear(x):
        z = (x-mean)/scale
        if record['intercept']: z = np.c_[np.ones(len(z)), z]
        return z@coef+ym
    if record['family'] == 'ARX':
        out = []
        for u in plan:
            past = list(o['history']); inputs = [np.zeros(4)]*3; values = []
            for k in range(100):
                x = np.r_[np.concatenate(past[-4:][::-1]), u[k], np.concatenate(inputs[-3:][::-1])]
                value = linear(x[None])[0]; values.append(value); past.append(value); inputs.append(u[k])
            out.append(values)
        absolute = np.array(out); return absolute-absolute[0], absolute
    predictions = []
    for u in plan:
        x = lags(u)
        if record['family'].startswith('STATE'): x = np.c_[x, x*((float(o['rate'])-record['state_mean'])/record['state_sd'])]
        predictions.append(linear(x))
    delta = np.array(predictions); return delta, delta+o['history'][-1]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--raw', type=Path, required=True); parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--analysis', type=Path, required=True); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args(); began = time.perf_counter()
    preserved = json.loads(Path('reports/evidence/m003_2/preservation.json').read_text())['files']
    for name, digest in preserved.items(): assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
    raw_source = json.loads((args.raw/'provenance.json').read_text())
    assert raw_source['protocol_sha256'] == hashlib.sha256(Path('docs/research/007_M003_2_STATE_DEPENDENCE_PROTOCOL.md').read_bytes()).hexdigest()
    for name, digest in raw_source['source_hashes'].items():
        assert hashlib.sha256((Path('src')/name).read_bytes()).hexdigest() == digest
    seal = json.loads((args.models/'forecast_seal.json').read_text())
    for name, digest in seal['artifact_sha256'].items(): assert hashlib.sha256((args.models/name).read_bytes()).hexdigest() == digest
    expected = {f'n{n}_r{rep}' for n in range(10) for rep in range(26, 31)} | {f'n{n}_r31' for n in range(3)}
    assert {p.name for p in args.raw.glob('n*_r*')} == expected
    observation_checks = 0; trials = 0; unique_noise = set()
    for n in range(10):
        for rep in ((26, 27, 28, 29, 30, 31) if n < 3 else (26, 27, 28, 29, 30)):
            trial = args.raw/f'n{n}_r{rep}'; report = json.loads((trial/'trial.json').read_text()); assert report['status'] == 'complete'
            assert report['engine']['config']['network_id'] == n and report['engine']['config']['replicate_id'] == rep
            assert report['engine']['config']['root_seed'] == 20261018 and report['engine']['config']['dt_us'] == 100
            assert report['engine']['config']['efficacy'] == (0. if rep == 31 else 1.)
            old = json.loads(Path(f'reports/evidence/m003_1/results/raw/n{n}_r22/trial.json').read_text())
            assert report['engine']['metadata']['parameter_hashes'] == old['engine']['metadata']['parameter_hashes']
            assert report['recording'] == read(Path(f'reports/evidence/m003_1/results/raw/n{n}_r22/confirmation.npz'))['recording'].tolist()
            assert not set(np.array(report['recording']).ravel()) & set(np.array(report['stimulation']).ravel())
            backbone = read(trial/'backbone.npz'); check_observations(backbone); observation_checks += 1
            assert len(backbone['counts']) == 1750 and not backbone['delivered'].any()
            c = backbone['rates'][750:1250]; values = np.array([c[k-5:k].mean() for k in range(5, 501)])
            bounds = np.quantile(values, [.25, .75]); np.testing.assert_array_equal(bounds, report['bounds'])
            candidate_rates = [float(backbone['rates'][k-5:k].mean()) for k in range(1260, 1751, 10)]
            ledger_rates = [r['rate'] for r in report['candidates']]; np.testing.assert_array_equal(candidate_rates, ledger_rates)
            plan = read(trial/'plans.npz')['planned']
            slew = np.diff(np.concatenate([np.zeros((7, 1, 4)), plan], axis=1), axis=1)
            assert (plan >= 0).all() and (plan <= 120).all() and (plan.sum(axis=2) <= 240).all() and (abs(slew) <= 30).all()
            for s, threshold, relation in (('LOW', bounds[0], np.less_equal), ('HIGH', bounds[1], np.greater_equal)):
                index = np.flatnonzero(relation(candidate_rates, threshold))[0]; stop = 1260+index*10
                o = origin(args.raw, n, rep, s); assert int(o['time_us']) == stop*20000
                assert set(o) == {'history', 'input_history', 'rate', 'bounds', 'time_us'}
                np.testing.assert_array_equal(o['history'], backbone['rates'][stop-50:stop])
                assert float(o['rate']) == candidate_rates[index] and not o['input_history'].any()
                null = None
                for a, name in enumerate(NAMES):
                    d = read(trial/s/f'{name}.npz'); check_observations(d, o['history'][-1]); observation_checks += 1
                    np.testing.assert_array_equal(d['delivered'], plan[a]); assert int(d['time_us'][0, 0]) == stop*20000
                    for channel, ids in enumerate(report['recording']): assert d['counts'][:, channel].sum() == d['neurons'][ids].sum()
                    receipt = report['origins'][s]['receipts'][a]
                    assert receipt['exposure_pA_s'] == float(plan[a].sum()*.02) and receipt['violations'] == 0
                    if rep == 31:
                        if null is None: null = d
                        else:
                            for key in ('counts', 'rates', 'neurons', 'event_time_us', 'event_channel'): np.testing.assert_array_equal(d[key], null[key])
            noise_key = tuple(v['fine'] for _, v in sorted(report['engine']['noise_hashes'].items()))
            assert noise_key not in unique_noise; unique_noise.add(noise_key); trials += 1
    candidates = json.loads((args.models/'candidates.json').read_text()); selected = json.loads((args.models/'selected.json').read_text())
    half = json.loads((args.models/'half_selected.json').read_text()); choices = json.loads((args.models/'selection.json').read_text())
    validations = {}; coefficient_checks = 0
    for n in range(10):
        for family in FAMILIES:
            x, y, mean, sd = training(args.raw, n, (26, 27), family)
            for lam in LAMBDAS:
                record = candidates[f'n{n}_{family}_{lam}']['model']; estimate(x, y, record); coefficient_checks += 1
                assert record['state_mean'] == mean and record['state_sd'] == sd
                losses = []
                for s in ('LOW', 'HIGH'):
                    o = origin(args.raw, n, 28, s); plan = read(args.raw/f'n{n}_r28'/'plans.npz')['planned']
                    delta, absolute = forecast(record, o, plan)
                    yy = np.array([read(args.raw/f'n{n}_r28'/s/f'{name}.npz')['rates'] for name in NAMES])
                    p, truth = (absolute, yy) if family == 'ARX' else (delta[1:], (yy-yy[0])[1:])
                    losses.append(np.mean((p[:, :50].mean(axis=1)-truth[:, :50].mean(axis=1))**2))
                score = float(np.mean(losses)); np.testing.assert_allclose(score, candidates[f'n{n}_{family}_{lam}']['validation_mse'], atol=1e-12)
                validations.setdefault((family, lam), []).append(score)
            x, y, _, _ = training(args.raw, n, (26,), family); estimate(x, y, half[f'n{n}_{family}']); coefficient_checks += 1
    for family in FAMILIES:
        scored = [(float(np.mean(validations[(family, lam)])), -lam, lam) for lam in LAMBDAS]
        minimum = min(r[0] for r in scored)
        chosen = max(r[2] for r in scored if r[0] <= minimum+1e-12); assert chosen == choices['chosen'][family]
        for n in range(10): assert selected[f'n{n}_{family}'] == candidates[f'n{n}_{family}_{chosen}']['model']
    forecast_checks = 0
    for n in range(10):
        for rep in ((29, 30, 31) if n < 3 else (29, 30)):
            plan = read(args.raw/f'n{n}_r{rep}'/'plans.npz')['planned']
            for suffix, models in (('', selected), ('_half', half)):
                archived = read(args.models/f'n{n}_r{rep}{suffix}.npz')
                for m, family in enumerate(FAMILIES):
                    for s, stratum in enumerate(('LOW', 'HIGH')):
                        delta, absolute = forecast(models[f'n{n}_{family}'], origin(args.raw, n, rep, stratum), plan)
                        np.testing.assert_allclose(delta, archived['delta'][m, s], rtol=0, atol=1e-10)
                        np.testing.assert_allclose(absolute, archived['absolute'][m, s], rtol=0, atol=1e-10); forecast_checks += 1
    data = read(args.analysis/'data.npz'); errors = np.empty_like(data['errors']); abs_errors = np.empty_like(errors)
    half_errors = np.empty_like(data['half_errors'])
    widths = read(args.models/'intervals.npz')['widths']
    for n in range(10):
        for m, family in enumerate(FAMILIES):
            ee = [[] for _ in range(4)]
            for s in ('LOW', 'HIGH'):
                o = origin(args.raw, n, 28, s); plan = read(args.raw/f'n{n}_r28'/'plans.npz')['planned']
                delta, _ = forecast(selected[f'n{n}_{family}'], o, plan)
                yy = np.array([read(args.raw/f'n{n}_r28'/s/f'{name}.npz')['rates'] for name in NAMES]); truth = yy-yy[0]
                for h, size in enumerate((1, 10, 50, 100)): ee[h].extend(np.abs(delta[1:, :size].mean(axis=1)-truth[1:, :size].mean(axis=1)).ravel())
            np.testing.assert_allclose(widths[n, m], [np.quantile(e, .95, method='higher') for e in ee], atol=1e-10)
        for r, rep in enumerate((29, 30)):
            pred = read(args.models/f'n{n}_r{rep}.npz'); half_pred = read(args.models/f'n{n}_r{rep}_half.npz')
            for s, stratum in enumerate(('LOW', 'HIGH')):
                yy = np.array([read(args.raw/f'n{n}_r{rep}'/stratum/f'{name}.npz')['rates'] for name in NAMES]); truth = yy-yy[0]
                for h, size in enumerate((1, 10, 50, 100)):
                    np.testing.assert_allclose(data['actual'][n, r, s, :, h], truth[:, :size].mean(axis=1), atol=1e-12)
                    errors[n, r, :, s, :, h] = (pred['delta'][:, s, :, :size].mean(axis=2)-truth[:, :size].mean(axis=1))**2
                    half_errors[n, r, :, s, :, h] = (half_pred['delta'][:, s, :, :size].mean(axis=2)-truth[:, :size].mean(axis=1))**2
                    abs_errors[n, r, :, s, :, h] = (pred['absolute'][:, s, :, :size].mean(axis=2)-yy[:, :size].mean(axis=1))**2
    np.testing.assert_allclose(half_errors, data['half_errors'], atol=1e-12)
    np.testing.assert_allclose(errors, data['errors'], atol=1e-12); np.testing.assert_allclose(abs_errors, data['absolute_errors'], atol=1e-12)
    network = errors[:, :, :, :, 1:].mean(axis=(1, 3, 4, 6)); np.testing.assert_array_equal(network, data['network'])
    delta = network[:, 0, 2]-network[:, 1, 2]; relative = delta/np.maximum(network[:, 0, 2], .04)
    draws = np.random.Generator(np.random.PCG64(20261102)).integers(0, 10, (10000, 10))
    ci = np.quantile(delta[draws].mean(axis=1), [.025, .975]); control = network[:, 2, 2]-network[:, 1, 2]
    control_ci = np.quantile(control[draws].mean(axis=1), [.025, .975]); summary = json.loads((args.analysis/'comparison.json').read_text())
    g = summary['scientific_gate']; np.testing.assert_array_equal(ci, g['absolute_ci']); np.testing.assert_array_equal(control_ci, g['shuffled_improvement_ci'])
    magnitude = delta.mean() >= .04 and relative.mean() >= .1 and (delta > 0).sum() >= 8
    decision = 'PASS' if magnitude and ci[0] > 0 and control_ci[0] > 0 else 'HOLD' if magnitude else 'FAIL'
    assert decision == g['decision']
    report = dict(execution='PASS', scientific=decision, historical_files_preserved=len(preserved), complete_trials=trials,
                  observation_archives_checked=observation_checks, independent_coefficients=coefficient_checks,
                  independent_common_origin_forecasts=forecast_checks, wall_s=time.perf_counter()-began,
                  limitation='Independent equations in this session; not external replication or alternate simulator')
    args.output.write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
