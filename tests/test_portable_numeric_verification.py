"""Analytic checks for the approved bound implementation, including rejection."""
from pathlib import Path
import runpy

import numpy as np
import pytest


MODULE = runpy.run_path(str(Path(__file__).parents[1]/'tools/portable_numeric_verification.py'))
Ball = MODULE['Enclosure']
Failure = MODULE['CertificateFailure']


def test_cancellation_and_known_interval_product():
    a = Ball([[1., -1.]], [[.1, .1]])
    b = Ball([[1.], [1.]], [[.1], [.1]])
    result = a.product(b)
    assert result.contains(np.array([[.4]]))
    assert result.contains(np.array([[-.4]]))
    assert not result.contains(np.array([[1.]]))


def test_interval_denominator_and_tampering_fail_closed():
    with pytest.raises(Failure, match='positive RLS denominator'):
        Ball(1.).divide_positive(Ball(1., 2.))
    assert not Ball(np.array([1.]), 1e-14).contains(np.array([1.001]))
    with pytest.raises(Failure):
        Ball(np.array([np.nan]))
    with pytest.raises(Failure, match='Subnormal'):
        Ball(np.array([np.nextafter(0., 1.)]))


def test_exact_inputs_enclose_independent_scalar_product():
    a = np.array([[1e16, 1., -1e16]])
    b = np.ones((3, 1))
    result = Ball(a).product(Ball(b))
    assert result.contains(np.array([[0.]]))
    assert result.contains(np.array([[1.]]))


def test_new_suspend_fixture_authorization_rejects_other_edits(monkeypatch):
    verify = runpy.run_path('scripts/m017_reproduce.py')['verify_history']
    read = Path.read_bytes

    def altered(path):
        data = read(path)
        return data+b'\n# unauthorized\n' if path==Path('tests/test_suspend_clock.py') else data

    monkeypatch.setattr(Path, 'read_bytes', altered)
    with pytest.raises(AssertionError, match='Protected baseline path differs: tests/test_suspend_clock.py'):
        verify()


def test_planner_choice_requires_more_than_matching_nominal_action():
    q = np.arange(625, dtype=float)
    delivered = np.zeros((625, 100))
    ambiguous = Ball(np.ones(625), np.ones(625))
    with pytest.raises(Failure, match='tie membership'):
        MODULE['certify_choice'](ambiguous, 0, q, q, delivered)
    separated = Ball(np.r_[0., np.full(624, 2.)], 1e-14)
    MODULE['certify_choice'](separated, 0, q, q, delivered)


def test_rls_step_contains_independent_scalar_intercept_update():
    theta = Ball(np.zeros((41, 4)))
    covariance = Ball(np.eye(41))
    features = np.r_[1., np.zeros(40)]
    theta, covariance, lower = MODULE['rls_step'](theta, covariance, features, np.ones(4))
    expected_theta = np.zeros((41, 4))
    expected_theta[0] = 1/1.999
    expected_covariance = np.eye(41)/.999
    expected_covariance[0, 0] = 1/1.999
    assert lower > 0
    assert theta.contains(expected_theta)
    assert covariance.contains(expected_covariance)
