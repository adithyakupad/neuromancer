from fractions import Fraction
import os

import numpy as np
import pytest

from tools.m029_kernel import build, load
from tools.portable_numeric_verification import CertificateFailure


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    if 'M029_KERNEL_DIR' in os.environ:
        return load()
    directory = tmp_path_factory.mktemp('m029-kernel')/'build'
    assert build(directory) == 0
    return load(directory/'lib')


def test_ordered_residual_encloses_rational_oracle(kernel):
    rng = np.random.default_rng(29)
    a = rng.normal(size=(41, 41))
    b = rng.normal(size=(41, 4))
    offset = a@b
    radius = np.full_like(a, 2.**-43)
    magnitude = kernel.residual_magnitude(a, radius, b, offset, np.zeros_like(offset))
    for i in range(41):
        for j in range(4):
            terms = [Fraction(float(a[i, k]))*Fraction(float(b[k, j])) for k in range(41)]
            uncertainty = sum(Fraction(float(radius[i, k]))*abs(Fraction(float(b[k, j]))) for k in range(41))
            assert abs(Fraction(float(offset[i, j]))-sum(terms)) + uncertainty <= Fraction(float(magnitude[i, j]))


def test_ordered_residual_is_independent_of_input_alignment(kernel):
    rng = np.random.default_rng(30)
    left = rng.normal(size=(41, 41))
    right = rng.normal(size=(41, 4))
    padded = np.empty(left.size+1)
    shifted = padded[1:].reshape(left.shape)
    shifted[:] = left
    expected = kernel.ordered_dot4(left, right)
    assert expected.tobytes() == kernel.ordered_dot4(shifted, right).tobytes()
    with pytest.raises(CertificateFailure, match='underflow'):
        kernel.residual_magnitude(np.full((2, 2), 1e-210), np.zeros((2, 2)),
                                  np.full((2, 4), 1e-210), np.zeros((2, 4)), np.zeros((2, 4)))
