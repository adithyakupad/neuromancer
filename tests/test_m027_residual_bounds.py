"""Independent Decimal arithmetic tests; no archive values set tolerances."""
from decimal import Decimal, localcontext

import numpy as np
import pytest

from tools.m027_residual_bounds import (
    InformationCertificate, Enclosure, CertificateFailure, objective_from_means, residual_planner_costs,
)
from tools.portable_numeric_verification import certify_choice


def decimal_matrix(values):
    return [[Decimal.from_float(float(value)) for value in row] for row in values]


def decimal_product(left, right):
    return [[sum((a*b for a, b in zip(row, column)), Decimal(0))
             for column in zip(*right)] for row in left]


def contains_decimal(ball, values):
    lower = np.nextafter(ball.center-ball.radius, -np.inf)
    upper = np.nextafter(ball.center+ball.radius, np.inf)
    return all(Decimal.from_float(float(low)) <= value <= Decimal.from_float(float(high))
               for low, value, high in zip(lower.flat, np.asarray(values, dtype=object).flat, upper.flat))


@pytest.mark.parametrize('ill_conditioned', [False, True])
def test_gain_covariance_and_coefficient_against_decimal(ill_conditioned):
    with localcontext() as context:
        context.prec = 90
        initial_p = np.diag([1., 1e6 if ill_conditioned else 2.])
        initial_theta = np.array([[.25], [-.125]])
        certificate = InformationCertificate(initial_theta, initial_p)
        covariance = Enclosure(initial_p)
        theta = Enclosure(initial_theta)
        exact_p = decimal_matrix(initial_p)
        exact_theta = decimal_matrix(initial_theta)
        forgetting = Decimal.from_float(.999)
        for index in range(16):
            z = np.array([[1.], [(-1.)**index/8]])
            observed = np.array([[index/16]])
            exact_z = decimal_matrix(z)
            exact_zp = decimal_product(list(map(list, zip(*exact_z))), exact_p)
            denominator = forgetting+decimal_product(exact_zp, exact_z)[0][0]
            exact_gain = [[value[0]/denominator] for value in decimal_product(exact_p, exact_z)]
            exact_residual = Decimal.from_float(float(observed[0, 0]))-decimal_product(list(map(list, zip(*exact_z))), exact_theta)[0][0]
            exact_theta = [[value[0]+gain[0]*exact_residual] for value, gain in zip(exact_theta, exact_gain)]
            exact_outer = decimal_product(exact_gain, exact_zp)
            exact_p = [[(value-exact_outer[i][j])/forgetting for j, value in enumerate(row)] for i, row in enumerate(exact_p)]
            # Decimal symmetry is exact here; reproduce the explicit production order.
            exact_p = [[(exact_p[i][j]+exact_p[j][i])/2 for j in range(2)] for i in range(2)]
            zp = Enclosure(z.T).product(covariance)
            gain = covariance.product(Enclosure(z)).divide_positive(Enclosure(.999).add(zp.product(Enclosure(z))))
            assert contains_decimal(gain, exact_gain)
            residual = Enclosure(observed).subtract(Enclosure(z.T).product(theta))
            theta = theta.add(gain.product(residual))
            covariance = covariance.subtract(gain.product(zp)).divide_positive(Enclosure(.999))
            covariance = covariance.add(covariance.transpose).divide_positive(Enclosure(2.))
            assert contains_decimal(theta, exact_theta)
            assert contains_decimal(covariance, exact_p)
            certificate.update(z.ravel(), observed.ravel())
            state = certificate.state(theta.center, covariance.center)
            assert contains_decimal(Enclosure(theta.center, state['coefficient_radius']), exact_theta)
            assert contains_decimal(Enclosure(covariance.center, state['covariance_radius']), exact_p)


def test_functional_residual_keeps_information_history():
    certificate = InformationCertificate(np.zeros((2, 1)), np.eye(2))
    before = certificate.information.center.copy()
    certificate.update([1., 0.], [1.])
    assert certificate.updates == 1
    assert not np.array_equal(before, certificate.information.center)
    theta = np.array([[1/1.999], [0.]])
    covariance = np.diag([1/1.999, 1/.999])
    left = certificate.state(theta, covariance)
    changed = theta+np.array([[1e-8], [1.]])
    right = certificate.state(changed, covariance)
    query = Enclosure(np.array([[1., 0.]]))
    radius = certificate.functional_difference(query, covariance, left, right)
    actual = query.center@(changed-theta)
    assert np.all(np.abs(actual) <= radius)
    # A read of archived/comparison state does not reset or modify information.
    np.testing.assert_array_equal(certificate.information.center, np.diag([1.999, .999]))


def test_prediction_and_objective_decimal_enclosure():
    with localcontext() as context:
        context.prec = 90
        theta = np.array([[1e3, -1e3], [.125, .25]])
        query = np.array([[1., 3.], [1., -3.]])
        prediction = Enclosure(query).product(Enclosure(theta))
        exact = decimal_product(decimal_matrix(query), decimal_matrix(theta))
        assert contains_decimal(prediction, exact)
        target = .1
        cost = objective_from_means(prediction, target, np.array([.02, .03]), np.array([.001, .002]))
        exact_cost = [[sum((value-Decimal.from_float(target))**2 for value in row)
                       +Decimal.from_float(dose)+Decimal.from_float(switch)]
                      for row, dose, switch in zip(exact, [.02, .03], [.001, .002])]
        assert contains_decimal(cost.reshape((2, 1)), exact_cost)


def test_near_tie_remains_uncertifiable():
    q = np.arange(625, dtype=float)
    with pytest.raises(CertificateFailure, match='tie membership'):
        certify_choice(Enclosure(np.r_[0., 5e-13, np.ones(623)], 2e-12), 0, q, q, np.zeros((625, 100)))


def test_information_domain_guards():
    with pytest.raises(CertificateFailure, match='Singular'):
        InformationCertificate(np.zeros((2, 1)), np.zeros((2, 2)))
    with pytest.raises(CertificateFailure, match='forgetting'):
        InformationCertificate(np.zeros((2, 1)), np.eye(2), 0.)
    with pytest.raises(CertificateFailure, match='Subnormal'):
        Enclosure(np.nextafter(0., 1.))
    with pytest.raises(CertificateFailure, match='positive RLS denominator'):
        Enclosure(0.).divide_positive(Enclosure(0.))
    exact_zero = Enclosure(np.zeros((2, 2))).product(Enclosure(np.zeros((2, 2))))
    np.testing.assert_array_equal(exact_zero.radius, np.zeros((2, 2)))


def test_full_planner_cost_bound_with_independent_decimal_candidate():
    from neuromancer.predictive_planner import plan
    theta = np.zeros((41, 4))
    theta[0] = 2.
    theta[1] = .001
    theta[3] = .001
    covariance = np.eye(41)
    record = dict(mean=np.zeros(40), scale=np.ones(40), output_mean=np.ones(4))
    history = np.zeros((9, 4))
    certificate = InformationCertificate(theta, covariance)
    native = plan(record, theta, history, 4., 51_000_000, clock=lambda: 0)
    changed = theta.copy()
    changed[1] += 1e-13
    archived = plan(record, changed, history, 4., 51_000_000, clock=lambda: 0)
    cost, _, _ = residual_planner_costs(certificate, record, theta, covariance,
                                       changed, covariance, history, 4., native)
    assert cost.contains(archived['cost'])
    with localcontext() as context:
        context.prec = 90
        for candidate in [0, 312, 624]:
            delivered = decimal_matrix(native['bank'][candidate].reshape(2, 50))
            means = [Decimal(3)+Decimal(2)*Decimal.from_float(.001)*sum(row)/50 for row in delivered]
            tracking = sum((mean-4)**2 for mean in means)
            q = [value for row in delivered for value in row]
            dose = Decimal.from_float(.02)*sum(Decimal.from_float(.02)*(value/120)**2 for value in q)
            q0 = Decimal.from_float(native['q0']) if candidate==native['chosen'] else Decimal(candidate//25*5)
            q1 = Decimal(candidate%25*5)
            switch = Decimal.from_float(.01)*(q0**2+(q1-q0)**2)/120**2
            assert contains_decimal(cost.part(candidate).reshape((1, 1)), [[tracking+dose+switch]])
