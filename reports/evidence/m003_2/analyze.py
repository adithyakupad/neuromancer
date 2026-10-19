"""Reserved evaluator: run only after model forecast seal exists."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from neuromancer.calibration_diagnostic import save_json
from neuromancer.state_dependence import FAMILIES, gate, effect
from neuromancer.state_experiment import NAMES
from fit_models import load_origins, HORIZONS, STRATA


def csv_write(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def interval(x):
    x = np.asarray(x); draws = np.random.default_rng(20261102).integers(0, 10, (10000, 10))
    return np.quantile(x[draws].mean(axis=1), [.025, .975], axis=0).tolist()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--raw', type=Path, required=True); parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    seal = json.loads((args.models/'forecast_seal.json').read_text())
    for name, digest in seal['artifact_sha256'].items(): assert hashlib.sha256((args.models/name).read_bytes()).hexdigest() == digest
    args.output.mkdir(parents=True, exist_ok=False); began = time.perf_counter()
    models = json.loads((args.models/'selected.json').read_text()); widths = np.load(args.models/'intervals.npz')['widths']
    actual = np.empty((10, 2, 2, 7, 4, 4)); predictions = np.empty((10, 2, 5, 2, 7, 4, 4)); absolute = np.empty_like(predictions)
    errors = np.empty_like(predictions); half_errors = np.empty_like(predictions); abs_errors = np.empty_like(predictions)
    rows = []; sector_rows = []; origins_rows = []; lag_rows = []; ablations = []; null_rows = []
    for n in range(10):
        for r, rep in enumerate((29, 30)):
            origins = load_origins(args.raw, n, rep, True)
            forecasts = np.load(args.models/f'n{n}_r{rep}.npz'); half = np.load(args.models/f'n{n}_r{rep}_half.npz')
            for s, o in enumerate(origins):
                y = o['y']; delta = y-y[0]
                for h, size in enumerate(HORIZONS):
                    actual[n, r, s, :, h] = delta[:, :size].mean(axis=1)
                    for m, family in enumerate(FAMILIES):
                        p = forecasts['delta'][m, s, :, :size].mean(axis=1); ab = forecasts['absolute'][m, s, :, :size].mean(axis=1)
                        truth = actual[n, r, s, :, h]; residual = p-truth
                        predictions[n, r, m, s, :, h] = p; absolute[n, r, m, s, :, h] = ab
                        errors[n, r, m, s, :, h] = residual**2
                        half_errors[n, r, m, s, :, h] = (half['delta'][m, s, :, :size].mean(axis=1)-truth)**2
                        abs_errors[n, r, m, s, :, h] = (ab-y[:, :size].mean(axis=1))**2
                        for a, name in enumerate(NAMES):
                            row = dict(network=n, replicate=rep, stratum=STRATA[s], action=name, model=family, horizon_ms=size*20,
                                       mse_hz2=float(np.mean(residual[a]**2)), bias_hz=float(residual[a].mean()),
                                       actual_effect_hz=float(truth[a].mean()), predicted_effect_hz=float(p[a].mean()),
                                       absolute_mse_hz2=float(abs_errors[n, r, m, s, a, h].mean()),
                                       coverage=float(np.mean(np.abs(residual[a]) <= widths[n, m, h])), interval_halfwidth_hz=float(widths[n, m, h]))
                            rows.append(row)
                            for sector in range(4): sector_rows.append(dict(**{k: row[k] for k in ('network', 'replicate', 'stratum', 'action', 'model', 'horizon_ms')},
                                sector=sector, actual_effect_hz=float(truth[a, sector]), prediction_hz=float(p[a, sector]), squared_error_hz2=float(residual[a, sector]**2)))
                for m, family in enumerate(FAMILIES):
                    residual = forecasts['delta'][m, s]-delta
                    for a in range(1, 7):
                        for sector in range(4):
                            q = residual[a, :, sector]; constant = np.std(q[:-1]) == 0 or np.std(q[1:]) == 0
                            lag_rows.append(dict(network=n, replicate=rep, stratum=STRATA[s], model=family, action=NAMES[a], sector=sector,
                                                lag1=0. if constant else float(np.corrcoef(q[:-1], q[1:])[0, 1]), constant=constant))
                rec = models[f'n{n}_STATE']; neutral = np.array([effect(rec, u, rec['state_mean']) for u in o['plan']])
                ablations.append(dict(network=n, replicate=rep, stratum=STRATA[s],
                    origin_mean_replacement_rms_hz=float(np.sqrt(np.mean((neutral-forecasts['delta'][1, s])**2))),
                    neutral_one_second_mse_hz2=float(np.mean((neutral[1:, :50].mean(axis=1)-delta[1:, :50].mean(axis=1))**2))))
        if n < 3:
            origins = load_origins(args.raw, n, 31, True); p = np.load(args.models/f'n{n}_r31.npz')['delta']
            for s, o in enumerate(origins):
                for j in range(7): np.testing.assert_array_equal(o['y'][j], o['y'][0])
                for m, family in enumerate(FAMILIES): null_rows.append(dict(network=n, replicate=31, stratum=STRATA[s], model=family,
                    actual_effect_max_hz=0., predicted_rms_hz=float(np.sqrt(np.mean(p[m, s, 1:]**2))),
                    one_second_false_response_rms_hz=float(np.sqrt(np.mean(p[m, s, 1:, :50].mean(axis=1)**2)))))
    for n in range(10):
        for rep in ((26, 27, 28, 29, 30, 31) if n < 3 else (26, 27, 28, 29, 30)):
            report = json.loads((args.raw/f'n{n}_r{rep}'/'trial.json').read_text())
            for stratum, o in report['origins'].items():
                origins_rows.append(dict(network=n, replicate=rep, stratum=stratum, origin_s=o['time_us']/1e6, rate_hz=o['rate'],
                                         q25=report['bounds'][0], q75=report['bounds'][1], preceding_exposure_pA_s=0.))
    # Axes n,repeat,model,stratum,action,horizon,sector. Sham excluded from primary.
    network = errors[:, :, :, :, 1:].mean(axis=(1, 3, 4, 6))
    half_network = half_errors[:, :, :, :, 1:].mean(axis=(1, 3, 4, 6))
    absolute_network = abs_errors.mean(axis=(1, 3, 4, 6))
    decision = gate(network[:, 0, 2], network[:, 1, 2], network[:, 2, 2])
    network_rows = [dict(network=n, model=family, horizon_ms=size*20, mse_hz2=float(network[n, m, h]),
                         half_data_mse_hz2=float(half_network[n, m, h]), absolute_mse_hz2=float(absolute_network[n, m, h]))
                    for n in range(10) for m, family in enumerate(FAMILIES) for h, size in enumerate(HORIZONS)]
    interaction = (actual[:, :, 1, 1:]-actual[:, :, 0, 1:]).mean(axis=(1, 2))
    summary = dict(scientific_gate=decision, model_mean_mse_hz2={f: network[:, m].mean(axis=0).tolist() for m, f in enumerate(FAMILIES)},
                   absolute_mean_mse_hz2={f: absolute_network[:, m].mean(axis=0).tolist() for m, f in enumerate(FAMILIES)},
                   half_data_mean_mse_hz2={f: half_network[:, m].mean(axis=0).tolist() for m, f in enumerate(FAMILIES)},
                   interaction_mean_hz=interaction.mean(axis=0).tolist(), interaction_ci=interval(interaction),
                   analysis_wall_s=time.perf_counter()-began, primary_horizon_ms=1000,
                   forecast_seal_sha256=hashlib.sha256((args.models/'forecast_seal.json').read_bytes()).hexdigest())
    for name, table in (('episodes', rows), ('sectors', sector_rows), ('networks', network_rows), ('origins', origins_rows),
                        ('residual_lag1', lag_rows), ('origin_ablation', ablations), ('null', null_rows)):
        csv_write(args.output/f'{name}.csv', table)
    np.savez_compressed(args.output/'data.npz', actual=actual, predicted=predictions, absolute=absolute, errors=errors,
                        half_errors=half_errors, absolute_errors=abs_errors, network=network, half_network=half_network,
                        absolute_network=absolute_network, interaction=interaction)
    save_json(args.output/'comparison.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
