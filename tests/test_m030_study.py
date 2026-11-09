from fractions import Fraction

import numpy as np

from tools.m029_fits import Ball, endpoints
from tools.m030_trace import first_difference
from tools.m030_v1 import bias_trajectory


def test_bias_recurrence_encloses_independent_exact_rational_trajectory():
    class Deadline:
        def check(self):
            pass

    slope = np.tile([[[.25, -.125]]], (8, 1, 1))
    centered = np.tile([[[.75, .375]]], (8, 1, 1))
    start = np.array([[.5, -.25]])
    intercept, prediction, bias = bias_trajectory(slope, abs(slope), Ball(start), Ball(1./1550.),
        centered, np.zeros((1, 2)), Deadline())
    lower, upper = endpoints(intercept)
    pl, pu = endpoints(prediction)
    bl, bu = endpoints(bias)
    values = list(map(Fraction, start[0]))
    gain = Fraction(1./1550.)
    for step in range(8):
        predicted = [value+Fraction(term) for value, term in zip(values, slope[step, 0], strict=True)]
        gain = gain/(Fraction(.999)+gain)
        assert Fraction(bl[step]) <= gain <= Fraction(bu[step])
        for j, expected in enumerate(predicted):
            assert Fraction(pl[step, 0, j]) <= expected <= Fraction(pu[step, 0, j])
            values[j] += gain*(Fraction(centered[step, 0, j])-expected)
            assert Fraction(lower[step+1, 0, j]) <= values[j] <= Fraction(upper[step+1, 0, j])


def test_first_difference_uses_binary64_bits_and_chronological_order():
    first = np.array([[1., 0.], [1., 1.]])
    second = first.copy()
    second[0, 1] = -0.
    second[1, 0] = np.nextafter(1., np.inf)
    mismatch = first_difference(first, second)
    assert mismatch['index'] == [0, 1]
    assert mismatch['bits'] == ['0x0000000000000000', '0x8000000000000000']
    assert first_difference(first, first) is None
