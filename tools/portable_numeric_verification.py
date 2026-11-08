"""Prospective operation-derived enclosures. No package algorithm is replaced."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np


UNIT_ROUNDOFF = np.finfo(np.float64).eps / 2


class CertificateFailure(ArithmeticError):
    pass


def upward(value):
    value = np.asarray(value, dtype=np.float64)
    if not np.isfinite(value).all() or np.any(value < 0):
        raise CertificateFailure('Nonfinite or negative radius')
    if np.any((value > 0) & (value < np.finfo(np.float64).tiny)):
        raise CertificateFailure('Radius underflow needs a separate arithmetic model')
    return np.where(value == 0, 0., np.nextafter(value, np.inf))


def checked_divide(numerator, denominator):
    quotient = np.asarray(numerator)/np.asarray(denominator)
    if np.any((np.asarray(numerator) != 0) & (np.abs(quotient) < np.finfo(np.float64).tiny)):
        raise CertificateFailure('Division underflow needs a separate arithmetic model')
    return quotient


def positive_add(a, b):
    return upward(np.asarray(a) + np.asarray(b))


def positive_multiply(a, b):
    a, b = np.broadcast_arrays(np.asarray(a), np.asarray(b))
    product = a * b
    if np.any((a > 0) & (b > 0) & (product < np.finfo(np.float64).tiny)):
        raise CertificateFailure('Radius product underflow needs a separate arithmetic model')
    return upward(product)


def gamma(length):
    error = length * UNIT_ROUNDOFF
    if not 0 <= error < 1:
        raise CertificateFailure('Dot-product error model is invalid')
    return np.nextafter(error/(1-error), np.inf)


def positive_product(a, b):
    # Nonnegative dot products have no cancellation. Inflate for their own rounding.
    a = np.asarray(a)
    b = np.asarray(b)
    positive_a = a[a > 0]
    positive_b = b[b > 0]
    if len(positive_a) and len(positive_b):
        # Conservative domain check also detects products rounded all the way to zero.
        if positive_a.min() < np.finfo(np.float64).tiny/positive_b.min():
            raise CertificateFailure('Dot-product underflow needs a separate arithmetic model')
    product = a @ b
    return upward(product/(1-gamma(a.shape[-1])))


class Enclosure:
    """Binary64 center and nonnegative radius, same shape and explicit operation order."""
    def __init__(self, center, radius=0.):
        self.center = np.asarray(center, dtype=np.float64)
        self.radius = np.broadcast_to(np.asarray(radius, dtype=np.float64), self.center.shape).copy()
        if not np.isfinite(self.center).all() or not np.isfinite(self.radius).all() or np.any(self.radius < 0):
            raise CertificateFailure('Invalid enclosure')
        if np.any((self.radius > 0) & (self.radius < np.finfo(np.float64).tiny)):
            raise CertificateFailure('Radius underflow needs a separate arithmetic model')
        if np.any((np.abs(self.center) > 0) & (np.abs(self.center) < np.finfo(np.float64).tiny)):
            raise CertificateFailure('Subnormal center needs a separate underflow model')

    def reshape(self, shape):
        return Enclosure(self.center.reshape(shape), self.radius.reshape(shape))

    @property
    def transpose(self):
        return Enclosure(self.center.T, self.radius.T)

    def add(self, other):
        center = self.center + other.center
        if np.any((center == 0) & (self.center != -other.center)):
            raise CertificateFailure('Addition underflow or non-IEEE arithmetic')
        # Twice the local roundoff covers two permitted floating evaluation paths.
        rounding = positive_multiply(2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF), np.abs(center))
        radius = positive_add(positive_add(self.radius, other.radius), rounding)
        return Enclosure(center, radius)

    def negative(self):
        return Enclosure(-self.center, self.radius)

    def subtract(self, other):
        return self.add(other.negative())

    def part(self, item):
        return Enclosure(self.center[item], self.radius[item])

    def multiply(self, other):
        center = self.center * other.center
        if np.any((self.center != 0) & (other.center != 0) & (np.abs(center) < np.finfo(np.float64).tiny)):
            raise CertificateFailure('Product underflow needs a separate arithmetic model')
        radius = positive_add(positive_multiply(np.abs(self.center), other.radius),
                              positive_multiply(self.radius, np.abs(other.center)))
        radius = positive_add(radius, positive_multiply(self.radius, other.radius))
        rounding = positive_multiply(2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF), np.abs(center))
        return Enclosure(center, positive_add(radius, rounding))

    def mean(self, axes):
        count = int(np.prod([self.center.shape[axis] for axis in axes]))
        center = self.center.mean(axis=axes)
        radius = upward(self.radius.sum(axis=axes)/(1-gamma(count)))
        magnitude = upward(np.abs(self.center).sum(axis=axes)/(1-gamma(count)))
        radius = positive_add(radius, positive_multiply(2*gamma(count), magnitude))
        radius = upward(checked_divide(radius, count))
        radius = positive_add(radius, positive_multiply(2*UNIT_ROUNDOFF, np.abs(center)))
        return Enclosure(center, radius)

    def product(self, other):
        center = self.center @ other.center
        radius = positive_add(positive_product(np.abs(self.center), other.radius),
                              positive_product(self.radius, np.abs(other.center)))
        radius = positive_add(radius, positive_product(self.radius, other.radius))
        rounding = positive_multiply(2*gamma(self.center.shape[-1]),
                                     positive_product(np.abs(self.center), np.abs(other.center)))
        return Enclosure(center, positive_add(radius, rounding))

    def divide_positive(self, denominator):
        lower = np.nextafter(denominator.center-denominator.radius, -np.inf)
        if not np.all(lower > 0):
            raise CertificateFailure('Cannot certify a positive RLS denominator')
        center = checked_divide(self.center, denominator.center)
        error = positive_add(self.radius, positive_multiply(np.abs(center), denominator.radius))
        radius = upward(checked_divide(error, lower))
        rounding = positive_multiply(2*UNIT_ROUNDOFF/(1-UNIT_ROUNDOFF), np.abs(center))
        return Enclosure(center, positive_add(radius, rounding))

    def contains(self, value):
        value = np.asarray(value)
        if value.shape != self.center.shape or value.dtype != np.float64:
            return False
        lower = np.nextafter(self.center-self.radius, -np.inf)
        upper = np.nextafter(self.center+self.radius, np.inf)
        return bool(np.all((value >= lower) & (value <= upper)))


def rls_step(theta, covariance, features, observed):
    """Original RLS order, with every intermediate uncertainty propagated."""
    forgetting = Enclosure(.999)
    z = Enclosure(features).reshape((41, 1))
    row = z.transpose
    z_p = row.product(covariance)
    denominator = forgetting.add(z_p.product(z))
    gain = covariance.product(z).divide_positive(denominator)
    residual = Enclosure(observed).reshape((1, 4)).subtract(row.product(theta))
    next_theta = theta.add(gain.product(residual))
    next_covariance = covariance.subtract(gain.product(z_p)).divide_positive(forgetting)
    next_covariance = next_covariance.add(next_covariance.transpose).divide_positive(Enclosure(2.))
    return next_theta, next_covariance, float(np.min(denominator.center-denominator.radius))


def certify_trajectory(output):
    """Fixed feasibility gate before any full archive verifier can be qualified."""
    from neuromancer.predictive import FIRModel
    output.mkdir(parents=True, exist_ok=False)
    fixture = runpy.run_path('tests/test_predictive.py')['fixture']()
    initial, _, _, inputs, rates = fixture
    model = FIRModel(initial.record, initial.information_inverse, 'RLS')
    theta = Enclosure(model.theta)
    covariance = Enclosure(model.p)
    rows = []
    failure = None
    # Count and sequence were frozen in FINAL_RESOLUTION_APPROVAL before execution.
    for index in range(256):
        k = 2400 + index % 100
        x = np.concatenate([inputs[k-lag] for lag in range(10)])
        z = model.standardized(x)
        observed = rates[k]-np.asarray(model.record['output_mean'])
        try:
            theta, covariance, lower = rls_step(theta, covariance, z, observed)
            model.update(x, rates[k])
            if model.failure is not None:
                raise CertificateFailure('Native model failed: '+model.failure)
            if not theta.contains(model.theta) or not covariance.contains(model.p):
                raise CertificateFailure('Native state escaped the arithmetic enclosure')
            rows.append(dict(step=index+1, theta_radius=float(theta.radius.max()),
                             covariance_radius=float(covariance.radius.max()), denominator_lower=lower))
        except CertificateFailure as exc:
            failure = dict(step=index+1, reason=str(exc), native_failure=model.failure,
                           theta_radius=float(theta.radius.max()),
                           covariance_radius=float(covariance.radius.max()))
            break
    result = dict(contract='operation-derived-portability-v1', prescribed_updates=256,
                  certified_updates=len(rows), initial_state='shared exact initialization',
                  trajectory_feasibility_pass=failure is None, full_archive_verifier_qualified=False,
                  failure=failure, trace=rows)
    # Even a complete pilot is only a prerequisite, never complete archive qualification.
    result['release_qualified'] = False
    (output/'certificate.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    np.savez_compressed(output/'last-state.npz',theta=model.theta,covariance=model.p,
                        theta_center=theta.center,theta_radius=theta.radius,
                        covariance_center=covariance.center,covariance_radius=covariance.radius)
    print(json.dumps({key:value for key,value in result.items() if key!='trace'}))
    return 0 if failure is None else 1


def planner_enclosure(record, theta, history, target):
    from neuromancer.predictive_planner import bank
    q0, q1, delivered = bank(history[-1, 0])
    scale = Enclosure(np.asarray(record['scale'])[:, None])
    b = theta.part(slice(1, None)).divide_positive(scale)
    offset = Enclosure(np.asarray(record['output_mean'])).add(theta.part(0))
    offset = offset.subtract(Enclosure(np.asarray(record['mean'])[None, :]).product(b).reshape((4,)))
    kernels = b.reshape((10, 4, 4))
    kernel = kernels.part((slice(None), 0, slice(None))).add(kernels.part((slice(None), 2, slice(None))))
    full = np.c_[np.broadcast_to(history[:, 0], (625, 9)), delivered]
    prediction = Enclosure(np.broadcast_to(offset.center, (625, 100, 4)),
                           np.broadcast_to(offset.radius, (625, 100, 4)))
    for lag in range(10):
        prediction = prediction.add(Enclosure(full[:, 9-lag:109-lag, None]).multiply(kernel.part(lag)))
    if np.max(np.abs(prediction.center)+prediction.radius) > 100:
        raise CertificateFailure('Candidate prediction enclosure crosses existing 100 Hz guard')
    means = prediction.reshape((625, 2, 50, 4)).mean((2, 3))
    error = means.subtract(Enclosure(target))
    tracking = error.multiply(error)
    # Sum two horizon losses using the original mean reduction and exact scaling.
    tracking = tracking.mean((1,)).multiply(Enclosure(2.))
    dose = .02*np.sum(.02*(delivered/120)**2, axis=1)
    switch = .01*((q0-history[-1, 0])**2+(q1-q0)**2)/120**2
    costs = tracking.add(Enclosure(dose, positive_multiply(2*gamma(105), np.abs(dose))))
    costs = costs.add(Enclosure(switch, positive_multiply(2*gamma(12), np.abs(switch))))
    return costs, q0, q1, delivered


def certify_choice(costs, chosen, q0, q1, delivered):
    lower = np.nextafter(costs.center-costs.radius, -np.inf)
    upper = np.nextafter(costs.center+costs.radius, np.inf)
    other = np.arange(625) != chosen
    if upper[chosen] > lower[other].min()+1e-12:
        raise CertificateFailure('Cost enclosure cannot certify existing 1e-12 planner tie membership')
    exposure = delivered.sum(axis=1)*.04
    order = np.lexsort((q1, q0, exposure))
    higher = order[:int(np.flatnonzero(order == chosen)[0])]
    if len(higher) and np.any(lower[higher] <= upper.min()+1e-12):
        raise CertificateFailure('Cost enclosure permits a different lexicographic planner choice')


def certify_archive(output):
    from neuromancer.predictive import FIRModel
    from neuromancer.predictive_planner import plan
    from neuromancer.research_codec import model_digest
    from neuromancer.supervisor import Deadline, atomic_json
    root = Path('reports/evidence/v1_finish/m005b/primary')
    meta = json.loads((root/'provenance.json').read_text())
    deadline = Deadline.from_environment()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    failure = None
    hashes_different = 0
    completed = 0
    try:
        for network, replicate in meta['jobs']:
            directory = root/f'n{network}_r{replicate}'
            initial = json.loads((directory/'initial.json').read_text())
            starting = dict(np.load(directory/'initial.npz'))
            trial = json.loads((directory/'trial.json').read_text())
            for branch in trial['branches']:
                if branch['controller'] != 'RLS-MPC':
                    continue
                name = branch['name']
                data = dict(np.load(directory/(name+'.npz')))
                inputs = data['delivered']
                history = np.vstack([starting['history'], inputs])
                raw = data['counts'].reshape(len(inputs), 4, 5)[:, :, :4].sum(axis=2)/.4
                model = FIRModel(initial['record'], starting['p'], 'RLS')
                theta = Enclosure(model.theta)
                covariance = Enclosure(model.p)
                for step in range(len(inputs)):
                    deadline.check()
                    if step % 50 == 0:
                        saved = dict(np.load(directory/f'{name}_plan_{step//50:02}.npz'))
                        if not theta.contains(saved['theta']):
                            raise CertificateFailure('Archived planner coefficients escape propagated enclosure')
                        past = history[step:step+9]
                        costs, q0, q1, bank = planner_enclosure(model.record, theta, past,
                                                             initial['calibration']['target_hz'])
                        if not costs.contains(saved['cost']):
                            raise CertificateFailure('Archived candidate costs escape propagated enclosure')
                        native = plan(model.record, model.theta, past, initial['calibration']['target_hz'],
                                      int(saved['origin_us']), clock=lambda: 0)
                        chosen = int(saved['chosen'])
                        if native['chosen'] != chosen:
                            raise CertificateFailure('Selected planner action differs from archive')
                        certify_choice(costs, chosen, q0, q1, bank)
                        if not np.array_equal(inputs[step:step+50, 0], bank[chosen, :50]):
                            raise CertificateFailure('Delivered action differs from certified policy')
                    x = history[step:step+10][::-1].ravel()
                    z = model.standardized(x)
                    eligible = int(data['frames'][step, 5]) > model.updates
                    if eligible:
                        theta, covariance, lower = rls_step(theta, covariance, z,
                                                           raw[step]-model.record['output_mean'])
                    model.update(x, raw[step], eligible)
                    if model.failure is not None:
                        raise CertificateFailure('Native RLS failure: '+model.failure)
                    if not theta.contains(model.theta) or not covariance.contains(model.p):
                        raise CertificateFailure('Native state escapes propagated enclosure')
                    hashes_different += model_digest(model) != data['state_hashes'][step].tobytes()
                    if (step+1) % 50 == 0:
                        checkpoint = (step+1)//50-1
                        if not theta.contains(data['dense_theta'][checkpoint]) or not covariance.contains(data['dense_p'][checkpoint]):
                            raise CertificateFailure('Archived dense state escapes propagated enclosure')
                        rows.append(dict(network=network, replicate=replicate, branch=name, step=step+1,
                                         theta_radius=float(theta.radius.max()),
                                         covariance_radius=float(covariance.radius.max())))
                        atomic_json(output/'progress.json', dict(rows=rows, hash_mismatches=int(hashes_different)))
                completed += 1
    except (CertificateFailure, TimeoutError) as exc:
        failure = dict(network=network, replicate=replicate, branch=name, step=step,
                       reason=str(exc), native_failure=model.failure,
                       theta_radius=float(theta.radius.max()), covariance_radius=float(covariance.radius.max()))
    result = dict(contract='operation-derived-portability-v1', completed_rls_branches=completed,
                  prescribed_rls_branches=40, failure=failure, checkpoints=rows,
                  recomputed_hash_mismatches=int(hashes_different),
                  rls_archive_certificate_pass=failure is None and completed == 40,
                  release_qualified=False)
    atomic_json(output/'certificate.json', result)
    print(json.dumps({key:value for key,value in result.items() if key!='checkpoints'}))
    return 0 if result['rls_archive_certificate_pass'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--archive', action='store_true')
    arguments = parser.parse_args()
    sys.exit(certify_archive(arguments.output) if arguments.archive else certify_trajectory(arguments.output))
