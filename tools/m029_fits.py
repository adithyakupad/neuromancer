"""Residual certificates for the saved M017 fit and recursive forecast fixtures."""
import hashlib
import json
from pathlib import Path

import numpy as np

from tools.m027_residual_bounds import InformationCertificate, norm_upper
from tools.m027_spectral_bounds import singular_values
from tools.portable_numeric_verification import (
    CertificateFailure, Enclosure as Ball, positive_add, positive_multiply,
)


def require(test, description):
    if not test:
        raise CertificateFailure(description)


def exact(expected, actual, label):
    expected, actual = np.asarray(expected), np.asarray(actual)
    require(expected.dtype == actual.dtype and expected.shape == actual.shape
            and expected.tobytes() == actual.tobytes(), f'Exact identity differs: {label}')


def fixed_inputs(name, *arrays):
    expected = json.loads(Path(__file__).with_name('m029_fixture_sha256.json').read_text())[name]
    actual = [dict(shape=list(x.shape), dtype=x.dtype.str,
                   sha256=hashlib.sha256(x.tobytes()).hexdigest()) for x in arrays]
    require(actual == expected, f'Fixed {name} input witness differs')


def members(ball, label, *values):
    for value in values:
        require(ball.contains(np.asarray(value, dtype=np.float64)), f'Outside enclosure: {label}')


def endpoints(ball):
    return np.nextafter(ball.center-ball.radius, -np.inf), np.nextafter(ball.center+ball.radius, np.inf)


def maximum(ball):
    return float(np.max(positive_add(abs(ball.center), ball.radius)))


def ridge(design, targets, regularization=.1):
    z = Ball(design)
    penalty = Ball(np.diag(np.r_[0., np.ones(z.center.shape[1]-1)]))
    penalty = penalty.multiply(Ball(float(len(design)))).multiply(Ball(regularization))
    return InformationCertificate.from_equations(z.transpose.product(z).add(penalty),
                                                z.transpose.product(Ball(targets)))


def state_pair(certificate, theta, covariance, reference, reference_covariance):
    native = certificate.state(theta, covariance)
    archived = certificate.state(reference, reference_covariance)
    coefficient = Ball(theta, positive_add(native['coefficient_radius'], archived['coefficient_radius']))
    inverse = Ball(covariance, positive_add(native['covariance_radius'], archived['covariance_radius']))
    members(coefficient, 'fit coefficients', reference)
    members(inverse, 'fit covariance', reference_covariance)
    return coefficient, inverse, native, archived


def spectral(matrix, records, singular_key='singular_values', condition_key='condition', perturbation=0.):
    certificate = singular_values(matrix)
    lower = np.maximum(0., np.nextafter(certificate['lower']-perturbation, -np.inf))
    upper = np.nextafter(certificate['upper']+perturbation, np.inf)
    threshold = np.nextafter(np.finfo(float).eps * max(matrix.shape) * upper[0], np.inf)
    require(lower[-1] > threshold, 'Numerical rank boundary is undecidable')
    condition = (np.nextafter(lower[0]/upper[-1], -np.inf),
                 np.nextafter(upper[0]/lower[-1], np.inf))
    for row in records:
        if singular_key in row:
            observed = np.asarray(row[singular_key])
            require(observed.shape == lower.shape and np.all((lower <= observed) & (observed <= upper)),
                    'Recorded singular values escaped reconstruction certificate')
        if condition_key in row:
            require(condition[0] <= row[condition_key] <= condition[1],
                    'Recorded condition escaped reconstruction certificate')
    return dict(condition=list(condition), rank=len(lower), perturbation=perturbation,
                **{key: value for key, value in certificate.items() if np.ndim(value) == 0})


def initial_fit(fixture, arrays, records, candidate, candidate_records):
    initial, design, targets, inputs, rates = fixture
    fixed_inputs('predictive', design, targets, inputs, rates)
    exact(arrays['initial_design'], design, 'initial design')
    exact(arrays['initial_targets'], targets, 'initial targets')
    old = records['initial']
    for field in ('mean', 'scale', 'output_mean'):
        exact(old[field], initial.record[field], field)
    theta = np.asarray(initial.record['coef'])
    p = initial.information_inverse
    for key, value in [('design', design), ('targets', targets), ('theta', theta), ('information_inverse', p)]:
        exact(candidate['initial_'+key], value, f'repeated initial {key}')
    require(initial.record == candidate_records['initial'], 'Repeated initial fit record differs')
    fit = ridge(design, targets)
    coefficient, inverse, native, archived = state_pair(fit, theta, p,
        arrays['initial_theta'], arrays['initial_information_inverse'])
    require(np.count_nonzero(design[:, 2::4]) == np.count_nonzero(design[:, 4::4]) == 0
            and np.array_equal(design[:, 1::4], design[:, 3::4]), 'C02 structure differs')
    diagnostics = [old['diagnostics'], initial.record['diagnostics']]
    floating = {'reduced_condition', 'information_condition', 'singular_values', 'reduced_singular_values'}
    require({k: v for k, v in diagnostics[0].items() if k not in floating}
            == {k: v for k, v in diagnostics[1].items() if k not in floating},
            'Initial discrete diagnostics differ')
    full = singular_values(design)
    for row in diagnostics:
        s = np.asarray(row['singular_values'])
        require(row['rank'] == 11 and row['reduced_rank'] == 11
                and np.all((full['lower'] <= s) & (s <= full['upper'])), 'Initial rank or singular values differ')
    reduced = spectral(np.c_[design[:, 0], design[:, 1::4]], diagnostics,
                       'reduced_singular_values', 'reduced_condition')
    gram_radius = Ball(fit.information.radius)
    gram_perturbation = np.nextafter(np.sqrt(float(positive_multiply(
        norm_upper(gram_radius), norm_upper(gram_radius.transpose)))), np.inf)
    information = spectral(fit.information.center, diagnostics, '', 'information_condition',
                           perturbation=gram_perturbation)
    require(reduced['condition'][1] < 1e6 and information['condition'][1] < 1e12,
            'Initial conditioning guard cannot be certified')
    return dict(coefficient_radius=float(coefficient.radius.max()),
                covariance_radius=float(inverse.radius.max()),
                inverse_contractions=[native['contraction'], archived['contraction']],
                structural_rank=11, reduced_spectrum=reduced, information_spectrum=information,
                reconstruction_upper=full['reconstruction_upper'],
                left_orthogonality_upper=full['left_orthogonality_upper'],
                right_orthogonality_upper=full['right_orthogonality_upper'])


def complex_block(matrix):
    return np.block([[matrix.real, -matrix.imag], [matrix.imag, matrix.real]])


def magnitude_bounds(value):
    re, im = Ball(value.real), Ball(value.imag)
    lower, upper = endpoints(re.multiply(re).add(im.multiply(im)))
    return (np.maximum(0., np.nextafter(np.sqrt(np.maximum(0., lower)), -np.inf)),
            np.nextafter(np.sqrt(upper), np.inf))


def eigen_radius(companion):
    """Verified diagonal similarity and Gershgorin disks in real block form."""
    eigenvalues, eigenvectors = np.linalg.eig(companion.center)
    vectors = complex_block(eigenvectors)
    block = Ball(complex_block(companion.center.astype(complex)),
                 np.block([[companion.radius, np.zeros_like(companion.radius)],
                           [np.zeros_like(companion.radius), companion.radius]]))
    inverse = np.linalg.inv(vectors)
    certificate = InformationCertificate.from_equations(Ball(vectors), Ball(np.zeros((len(vectors), 1))))
    inverse_upper = certificate.state(np.zeros((len(vectors), 1)), inverse)['inverse_upper']
    residual = block.product(Ball(vectors)).subtract(
        Ball(vectors).product(Ball(complex_block(np.diag(eigenvalues)))))
    disk = float(positive_multiply(inverse_upper, norm_upper(residual)))
    lower, upper = magnitude_bounds(eigenvalues)
    # Conservatively merge disks whenever coordinate separation is undecidable.
    remaining = set(range(len(eigenvalues)))
    components = []
    while remaining:
        component = {remaining.pop()}
        while True:
            adjacent = {j for j in remaining if any(
                max(np.nextafter(abs(eigenvalues[i].real-eigenvalues[j].real), -np.inf),
                    np.nextafter(abs(eigenvalues[i].imag-eigenvalues[j].imag), -np.inf))
                <= np.nextafter(2*disk, np.inf) for i in component)}
            if not adjacent:
                break
            component |= adjacent
            remaining -= adjacent
        components.append(sorted(component))
    # An isolated component of k disks contains k eigenvalues.
    minimum = max(0., max(float(np.nextafter(lower[group].min()-disk, -np.inf)) for group in components))
    return minimum, float(positive_add(upper.max(), disk))


def join(parts):
    return Ball(np.concatenate([p.center for p in parts]), np.concatenate([p.radius for p in parts]))


def arx_fits(arrays, records, candidate, candidate_records, deadline):
    from neuromancer import identify

    rng = np.random.default_rng(20261104)
    u = rng.uniform(0, 30, (3300, 4))
    y = np.full((3300, 4), 8.)
    for i in range(1, len(y)):
        y[i] = 8 + .4*(y[i-1]-8) + .002*u[i] + rng.normal(0, .02, 4)
    fixed_inputs('arx', u, y)
    indices = np.arange(identify.FIT.start, identify.FIT.stop)
    rows = []
    for family in ('AR', 'ARX', 'SHUFFLED'):
        for lags in (1, 4):
            deadline.check()
            name = f'{family}{lags}'
            old, new = records[name], candidate_records[name]
            require(old['family'] == new['family'] == family and old['p'] == new['p'] == lags,
                    f'{name} model family or order changed')
            for field in ('mean', 'scale', 'output_mean'):
                exact(old[field], new[field], f'{name} {field}')
            current = u.copy()
            if family == 'SHUFFLED':
                current[identify.FIT] = np.roll(current[identify.FIT], 500, axis=0)
            x = identify.features(y, current, indices, lags, family != 'AR')
            exact(new['mean'], x.mean(axis=0), f'{name} fixture mean')
            exact(new['scale'], np.maximum(x.std(axis=0), 1), f'{name} fixture scale')
            exact(new['output_mean'], y[indices].mean(axis=0), f'{name} fixture output mean')
            z = np.c_[np.ones(len(x)), (x-new['mean'])/new['scale']]
            lam = new['diagnostics']['lambda_value']
            norm = np.sqrt(len(x))
            augmented = np.vstack([z/norm, np.diag(np.r_[0., np.full(z.shape[1]-1, np.sqrt(lam))])])
            target = np.vstack([(y[indices]-new['output_mean'])/norm, np.zeros((z.shape[1], 4))])
            # The augmented input is the fixed binary64 problem supplied to LAPACK.
            design = Ball(augmented)
            information = design.transpose.product(design)
            fit = InformationCertificate.from_equations(information, design.transpose.product(Ball(target)))
            inverse = np.linalg.inv(information.center)
            coefficient, _, native, archived = state_pair(fit, np.asarray(new['coef']), inverse,
                                                           np.asarray(old['coef']), inverse)
            diagnostics = [old['diagnostics'], new['diagnostics']]
            floating = {'condition', 'penalized_condition', 'spectral_radius', 'singular_values'}
            require({k: v for k, v in diagnostics[0].items() if k not in floating}
                    == {k: v for k, v in diagnostics[1].items() if k not in floating}
                    and all(d['valid'] for d in diagnostics), f'{name} discrete diagnostics differ')
            spec = spectral(z, diagnostics)
            regularized = spectral(augmented, diagnostics, '', 'penalized_condition')
            require(spec['rank'] == old['diagnostics']['rank'] == new['diagnostics']['rank']
                    and spec['condition'][1] <= 1e6 and regularized['condition'][1] <= 1e8,
                    f'{name} fit validity boundary')
            dynamic = coefficient.part(slice(1, 1+4*lags)).divide_positive(
                Ball(np.asarray(new['scale'][:4*lags])[:, None]))
            center, radius = np.zeros((4*lags, 4*lags)), np.zeros((4*lags, 4*lags))
            center[:4], radius[:4] = dynamic.center.T, dynamic.radius.T
            center[4:, :-4] = np.eye(4*(lags-1))
            low, high = eigen_radius(Ball(center, radius))
            require(high < .999 and all(low <= d['spectral_radius'] <= high for d in diagnostics),
                    f'{name} spectral guard or diagnostic outside enclosure')
            ys, us = [Ball(value) for value in y[3200-lags:3200]], list(u[3197:3200])
            forecast_radius = 0.
            for i, action in enumerate(u[3200:3250]):
                parts = [ys[-lag] for lag in range(1, lags+1)]
                if family != 'AR':
                    parts.extend(Ball(value) for value in (action, *us[::-1]))
                feature = join(parts).subtract(Ball(new['mean'])).divide_positive(Ball(new['scale']))
                pred = Ball(new['output_mean']).add(join([Ball([1.]), feature]).product(coefficient))
                members(pred, f'{name} forecast {i}', arrays[name+'_prediction'][i],
                        candidate[name+'_prediction'][i])
                require(maximum(pred) <= 100, f'{name} forecast guard crossed')
                forecast_radius = max(forecast_radius, float(pred.radius.max()))
                ys.append(pred)
                us = [*us[1:], action]
            rows.append(dict(name=name, design=spec, augmented=regularized, spectrum=[low, high],
                coefficient_radius=float(coefficient.radius.max()), forecast_radius=forecast_radius,
                inverse_contractions=[native['contraction'], archived['contraction']]))
    return rows
