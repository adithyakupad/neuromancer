"""Continuous V1 bias-state proof and byte-authenticated first-digest witness."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from neuromancer.predictive import FIRModel
from neuromancer.research_codec import model_digest
from neuromancer.supervisor import Deadline, atomic_json
from tools.m027_residual_bounds import InformationCertificate
from tools.m029_fits import Ball, endpoints, exact, maximum, members, require, ridge
from tools.m029_remaining import archived_npz
from tools.portable_numeric_verification import gamma, positive_add, positive_multiply, positive_product

ROOT = Path('reports/evidence/v1_finish/m005b/primary')
WITNESS = Path('reports/engineering/evidence/m030_first_digest/reference.npz')


def read(path):
    return json.loads(path.read_text())


def raw_inputs(folder, branch, initial):
    data = archived_npz(folder/(branch+'.npz'))
    history = np.vstack([initial['history'], data['delivered']])
    x = np.lib.stride_tricks.sliding_window_view(history, 10, axis=0)
    x = x[:, :, ::-1].transpose(0, 2, 1).reshape(-1, 40)
    rates = data['counts'].reshape(-1, 4, 5)[:, :, :4].sum(axis=2)/.4
    return data, x, rates


def first_digest(output, reference=False):
    """Use the first original V1 RLS update and authenticate archived bytes."""
    folder = ROOT/'n0_r47'
    record = read(folder/'initial.json')['record']
    initial = archived_npz(folder/'initial.npz')
    data, x, rates = raw_inputs(folder, 'STATIC_RLS-MPC', initial)
    model = FIRModel(record, initial['p'], 'RLS')
    z = model.standardized(x[0])
    centered = rates[0]-record['output_mean']
    observed_digest = data['state_hashes'][0].tobytes()
    # Source-bound operation trace uses the same operand values and verifies
    # the resulting state against the actual untouched update below.
    from tools.m030_trace import native_update_probe
    operations = {}

    def observe(label, left, right):
        result = left @ right
        operations[label] = result.copy()
        return result

    update, labels, update_hash = native_update_probe(FIRModel.update, observe)
    probe = FIRModel(record, initial['p'], 'RLS')
    update(probe, x[0], rates[0])
    initial_digest = model_digest(model).hex()
    model.update(x[0], rates[0])
    require(model.failure is None, 'Native first update failed')
    fresh_digest = model_digest(model)
    observations = dict(theta=model.theta, covariance=model.p, bias=np.asarray(model.bias_p),
                        x=x[0], rate=rates[0], z=z, centered=centered)
    output.mkdir(parents=True, exist_ok=False)
    if reference:
        require(fresh_digest == observed_digest, 'Reference does not reproduce the first archived digest')
        np.savez_compressed(output/'reference.npz', **observations, **operations)
    else:
        with np.load(WITNESS, allow_pickle=False) as archive:
            archived = dict(archive)
        stored = FIRModel(record, initial['p'], 'RLS')
        stored.theta, stored.p, stored.bias_p = archived['theta'], archived['covariance'], archived['bias'].item()
        require(model_digest(stored) == observed_digest, 'Reference witness is not authenticated by the archived digest')
        for key in ('x', 'rate', 'z', 'centered'):
            exact(archived[key], observations[key], 'First archived update '+key)
        certificate = InformationCertificate(record['coef'], initial['p'])
        certificate.update(z, centered)
        native = certificate.state(model.theta, model.p)
        saved = certificate.state(stored.theta, stored.p)
        members(Ball(model.theta, positive_add(native['coefficient_radius'], saved['coefficient_radius'])),
                'First archived coefficients', stored.theta)
        members(Ball(model.p, positive_add(native['covariance_radius'], saved['covariance_radius'])),
                'First archived covariance', stored.p)
        exact(stored.bias_p, model.bias_p, 'First RLS bias state')
        from tools.m030_trace import first_difference
        differences = {key: diff for key, value in observations.items()
                       if (diff := first_difference(archived[key], value))}
        operator_differences = {key: diff for key in operations
                                if (diff := first_difference(archived[key], operations[key]))}
        atomic_json(output/'first-digest-proof.json', dict(branch='n0_r47 STATIC_RLS-MPC', index=0,
            archived_sha256=observed_digest.hex(), recomputed_sha256=fresh_digest.hex(),
            initial_sha256=initial_digest, native_update_source_sha256=update_hash,
            first_operator_difference=next(iter(operator_differences), None),
            operator_differences=operator_differences, state_differences=differences,
            reference_operand_probe_matches_actual=True, fresh_operand_probe_matches_actual=model_digest(probe)==fresh_digest,
            coefficient_radii=[float(native['coefficient_radius'].max()), float(saved['coefficient_radius'].max())],
            covariance_radii=[native['covariance_radius'], saved['covariance_radius']],
            immutable_archive_digest_verified=True, outward_state_check_pass=True))
        np.savez_compressed(output/'fresh.npz', **observations, **operations)
    if reference:
        require(model_digest(probe) == fresh_digest, 'Reference operand probe differs from original method')
    atomic_json(output/'metadata.json', dict(archived=observed_digest.hex(), recomputed=fresh_digest.hex(),
                reference=reference, operations=labels, update_sha256=update_hash))


def bias_trajectory(slope, slope_magnitude, intercept, bias, centered, means, deadline):
    """Carry one common enclosure for each independent archived bias branch."""
    forgetting = Ball(.999)
    trace, radius = [intercept.center.copy()], [intercept.radius.copy()]
    forecast, forecast_radius, scalar, scalar_radius = [], [], [], []
    factor = 2*gamma(41)

    def dot(at, state):
        separate = Ball(slope[at]).add(state)
        # The native dot includes the intercept as its first term. Charge
        # both dot evaluation orders against their absolute operand sum.
        magnitude = positive_add(slope_magnitude[at], positive_add(abs(state.center), state.radius))
        return Ball(separate.center, positive_add(separate.radius, positive_multiply(factor, magnitude)))

    for at in range(len(slope)):
        deadline.check()
        predicted_dot = dot(at, intercept)
        y = Ball(means).add(predicted_dot)
        require(maximum(y) <= 100., 'Bias forecast guard crossed')
        forecast.append(y.center.copy())
        forecast_radius.append(y.radius.copy())
        bias = bias.divide_positive(forgetting.add(bias))
        require(endpoints(bias)[0].item() > 0, 'Bias gain is not certified positive')
        residual = Ball(centered[at]).subtract(predicted_dot)
        intercept = intercept.add(bias.multiply(residual))
        require(maximum(Ball(means).add(dot(at, intercept))) <= 100., 'Bias updated forecast guard crossed')
        trace.append(intercept.center.copy())
        radius.append(intercept.radius.copy())
        scalar.append(bias.center.item())
        scalar_radius.append(bias.radius.item())
    return (Ball(np.asarray(trace), np.asarray(radius)), Ball(np.asarray(forecast), np.asarray(forecast_radius)),
            Ball(np.asarray(scalar), np.asarray(scalar_radius)))


def model_portability(output, deadline):
    """Audit all FIXED and BIAS model states on the original primary cohort."""
    output.mkdir(parents=True, exist_ok=False)
    fixtures, fits, results = [], [], []
    for network, replicate in read(ROOT/'provenance.json')['jobs']:
        deadline.check()
        folder = ROOT/f'n{network}_r{replicate}'
        initial = archived_npz(folder/'initial.npz')
        record = read(folder/'initial.json')['record']
        prefix = archived_npz(folder/'prefix.npz')
        inputs = prefix['delivered']
        rates = prefix['counts'].reshape(-1, 4, 5)[:, :, :4].sum(2)/.4
        k = np.arange(800, 2350)
        x = np.hstack([inputs[k-j] for j in range(10)])
        exact(record['mean'], x.mean(axis=0), 'V1 initial normalizer mean')
        exact(record['scale'], np.maximum(x.std(axis=0), 1.), 'V1 initial normalizer scale')
        exact(record['output_mean'], rates[k].mean(axis=0), 'V1 initial output mean')
        theta = np.asarray(record['coef'])
        design = np.c_[np.ones(len(x)), (x-record['mean'])/record['scale']]
        certificate = ridge(design, rates[k]-record['output_mean'])
        # Compare the saved fit with a fresh solve of the same design.
        actual_gram = design.T@design + len(x)*.1*np.diag(np.r_[0., np.ones(40)])
        rhs = design.T@(rates[k]-record['output_mean'])
        fresh = certificate.state(np.linalg.solve(actual_gram, rhs), np.linalg.inv(actual_gram))
        saved = certificate.state(theta, initial['p'])
        fits.append(dict(network=network, replicate=replicate,
                         contractions=[fresh['contraction'], saved['contraction']],
                         comparison_radius=float(positive_add(fresh['coefficient_radius'],
                                                               saved['coefficient_radius']).max())))
        for branch in read(folder/'trial.json')['branches']:
            kind = branch['controller']
            if kind not in ('FIXED-MPC', 'BIAS-MPC'):
                continue
            require(branch['bins'] == 3200 and not branch['fault'] and branch['model_failure'] is None
                    and branch['safe_bins'] == 0, 'Unsupported archived fallback branch')
            name = branch['name']
            data, history, y = raw_inputs(folder, name, initial)
            z = np.c_[np.ones(len(history)), (history-record['mean'])/record['scale']]
            require(data['presented'].all(), 'Archived input eligibility differs')
            np.testing.assert_array_equal(data['frames'][:, 4], np.arange(1, 3201))
            np.testing.assert_array_equal(data['frames'][:, 5],
                np.arange(1, 3201) if kind == 'BIAS-MPC' else np.zeros(3200))
            np.testing.assert_array_equal(data['frames'][:, 6:], np.zeros((3200, 2)))
            frozen = np.broadcast_to(initial['p'], data['dense_p'].shape)
            exact(frozen, data['dense_p'], 'Unchanged archived covariance')
            exact(np.broadcast_to(theta[1:], data['dense_theta'][:, 1:].shape),
                  data['dense_theta'][:, 1:], 'Unchanged archived FIR slopes')
            if kind == 'FIXED-MPC':
                model = FIRModel(record, initial['p'], 'FIXED')
                exact(np.broadcast_to(np.frombuffer(model_digest(model), dtype=np.uint8), data['state_hashes'].shape),
                      data['state_hashes'], 'Every immutable fixed state digest')
                exact(np.broadcast_to(theta, data['dense_theta'].shape), data['dense_theta'], 'Fixed coefficient snapshots')
                exact(np.full(64, model.bias_p), data['dense_bias'], 'Fixed scalar covariance snapshots')
                prediction = Ball(record['output_mean']).add(Ball(z).product(Ball(theta)))
                require(maximum(prediction) <= 100., 'Fixed forecast guard crossed')
                members(prediction, 'Fixed archived per-bin forecasts', data['pre_prediction'])
                results.append(dict(branch=[network, replicate, name], states=3200, forecasts=3200,
                                    exact_state_digests=3200, float_differences=0))
            else:
                fixtures.append(dict(branch=[network, replicate, name], record=record, initial=initial,
                    observed=data['state_hashes'], theta=data['dense_theta'], bias=data['dense_bias'],
                    predictions=data['pre_prediction'], history=history, z=z, y=y,
                    slope=z[:, 1:]@theta[1:], magnitude=positive_product(abs(z[:, 1:]), abs(theta[1:]))))

    require(len(fixtures) == len(results) == 40, 'Unexpected V1 model scope')
    centers = np.asarray([f['record']['coef'][0] for f in fixtures])
    means = np.asarray([f['record']['output_mean'] for f in fixtures])
    stack = lambda key: np.stack([f[key] for f in fixtures], axis=1)
    require(all(f['record']['diagnostics']['rows'] == 1550 for f in fixtures), 'Bias initial information differs')
    bounds, forecasts, scalar = bias_trajectory(stack('slope'), stack('magnitude'),
        Ball(centers), Ball(1./1550.), stack('y')-means, means, deadline)
    for j, fixture in enumerate(fixtures):
        deadline.check()
        member = (slice(None), j)
        members(forecasts.part(member), 'Bias archived per-bin forecasts', fixture['predictions'])
        members(bounds.part((slice(50, None, 50), j)), 'Bias archived coefficient snapshots', fixture['theta'][:, 0])
        members(scalar.part(slice(49, None, 50)), 'Bias archived scalar covariance snapshots', fixture['bias'])
        model = FIRModel(fixture['record'], fixture['initial']['p'], 'BIAS')
        native_theta, native_bias, native_pred, digests = [], [], [], []
        for at, (x, y) in enumerate(zip(fixture['history'], fixture['y'], strict=True)):
            deadline.check()
            exact(model.standardized(x), fixture['z'][at], 'Native bias feature order')
            native_pred.append(model.predict(x))
            model.update(x, y)
            require(model.failure is None and model.updates == at+1, 'Native bias update failed')
            native_theta.append(model.theta[0].copy())
            native_bias.append(model.bias_p)
            digests.append(model_digest(model) == fixture['observed'][at].tobytes())
        members(bounds.part((slice(1, None), j)), 'Every native bias intercept update', np.asarray(native_theta))
        members(scalar, 'Every native scalar covariance update', np.asarray(native_bias))
        members(forecasts.part(member), 'Every native bias forecast', np.asarray(native_pred))
        exact(model.p, fixture['initial']['p'], 'Native unchanged bias model covariance')
        results.append(dict(branch=fixture['branch'], states=3200, forecasts=3200,
                            exact_state_digests=sum(digests), float_differences=3200-sum(digests)))
        atomic_json(output/'progress.json', dict(fits=fits, branches=results, release_qualified=False))
    report = dict(fits=fits, branches=results, model_states=sum(r['states'] for r in results),
                  max_bias_radius=float(bounds.radius.max()), max_forecast_radius=float(forecasts.radius.max()),
                  scope='FIXED and BIAS numerical states and forecasts', full_V1_portability=False)
    atomic_json(output/'certificate.json', report)
    return report, bounds, [tuple(f['branch']) for f in fixtures]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['reference', 'first', 'models'])
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.mode == 'models':
        model_portability(args.output, Deadline.from_environment())
    else:
        first_digest(args.output, reference=args.mode == 'reference')
