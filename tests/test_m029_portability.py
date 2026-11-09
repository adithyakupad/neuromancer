import numpy as np
import pytest

from tools.m029_fits import Ball, eigen_radius, exact, ridge, state_pair
from tools.m029_remaining import exact_reduction_at_half
from tools.portable_numeric_verification import CertificateFailure


def test_complex_eigenvalue_enclosure_covers_bounded_perturbations():
    matrix = np.array([[.1, -.2], [.2, .1]])
    perturbation = np.full((2, 2), 1e-8)
    lower, upper = eigen_radius(Ball(matrix, perturbation))
    assert 0 < lower < np.sqrt(.05) < upper < .999
    for i in range(16):
        signs = (2*(np.array([i >> shift & 1 for shift in range(4)])-.5)).reshape(2, 2)
        radius = abs(np.linalg.eigvals(matrix+perturbation*signs)).max()
        assert lower <= radius <= upper


def test_fit_validates_inverse_against_original_regularized_problem():
    x = np.c_[np.ones(3), [-1., 0., 1.]]
    y = np.array([[1.], [2.], [3.]])
    fit = ridge(x, y, .25)
    inverse = np.linalg.inv(x.T@x+np.diag([0., .75]))
    theta = np.array([[2.], [8/11]])
    coeff, _, _, _ = state_pair(fit, theta, inverse, theta, inverse)
    assert coeff.contains(theta)
    with pytest.raises(CertificateFailure, match='invertible'):
        state_pair(fit, theta, np.zeros_like(inverse), theta, inverse)


def test_exact_half_requires_representable_intermediates():
    assert exact_reduction_at_half(np.array([1., 0.]), np.array([.5, .1]))
    assert exact_reduction_at_half(np.array([1., 1.]), np.array([.25, .25]))
    assert not exact_reduction_at_half(np.ones(3), np.array([2.**54, .5, -2.**54]))
    assert not exact_reduction_at_half(np.ones(1), np.array([.49]))


def test_exact_discrete_replay_rejects_signed_zero_and_dtype_drift():
    with pytest.raises(CertificateFailure, match='Exact identity'):
        exact([0.], [-0.], 'actuator')
    with pytest.raises(CertificateFailure, match='Exact identity'):
        exact(np.array([1], dtype=np.int32), np.array([1], dtype=np.int64), 'spike')
