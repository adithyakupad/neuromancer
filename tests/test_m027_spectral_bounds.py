"""Analytic singular values and backward-residual regression tests."""
import numpy as np
import pytest

from tools.m027_residual_bounds import InformationCertificate, Enclosure, CertificateFailure
from tools.m027_spectral_bounds import singular_values, condition_interval


@pytest.mark.parametrize('matrix,expected', [
    (np.diag([3., 1.]), [3., 1.]),
    (np.array([[1., 1.], [1., -1.], [0., 0.]]), [np.sqrt(2.), np.sqrt(2.)]),
    (np.diag([1., 1e-8]), [1., 1e-8]),
    (np.diag([1., 0.]), [1., 0.]),
])
def test_known_singular_values(matrix, expected):
    result = singular_values(matrix)
    assert np.all(result['lower'] <= expected)
    assert np.all(result['upper'] >= expected)


def test_singular_condition_is_not_given_a_finite_certificate():
    with pytest.raises(CertificateFailure, match='no positive'):
        condition_interval(np.diag([1., 0.]))


def test_fixed_ridge_residual_has_independent_exact_solution():
    z = Enclosure(np.array([[1., 1.], [1., -1.]]))
    y = Enclosure(np.array([[3.], [1.]]))
    information = z.transpose.product(z).add(Enclosure(np.diag([0., 2.])))
    rhs = z.transpose.product(y)
    certificate = InformationCertificate.from_equations(information, rhs)
    state = certificate.state(np.array([[2.], [.5]]), np.diag([.5, .25]))
    assert state['contraction'] < 1
    assert np.max(state['coefficient_radius']) < 1e-12


def test_nonfinite_spectral_domain_is_rejected():
    with pytest.raises((CertificateFailure, np.linalg.LinAlgError)):
        singular_values(np.array([[np.nan, 1.], [0., 1.]]))
