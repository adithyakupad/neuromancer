"""Independent exact arithmetic and ULP boundary checks for read-only diagnostics."""
import runpy
from pathlib import Path

import numpy as np


TOOLS = runpy.run_path(str(Path(__file__).parents[1]/'tools/final_numeric_diagnosis.py'))


def test_ulp_distances_across_zero_and_adjacent_floats():
    difference = TOOLS['difference']
    result = difference(np.array([-1., 0., 1.]),
                        np.array([np.nextafter(-1., 0), -0., np.nextafter(1., 2.)]))
    assert result['max_ulp_distance'] == 1
    assert result['changed_finite_values'] == 2
    assert not difference(np.array([0.]), np.array([-0.]))['exact']
    assert difference(np.array([0.]), np.array([-0.]))['max_ulp_distance'] == 0
    assert difference(np.array([0.]), np.array([1.]))['zero_reference_nonzero_observed'] == 1


def test_serial_operations_known_exact_equations_and_pivot():
    a = np.array([[0., 2.], [1., 1.]])
    b = np.array([[2.], [3.]])
    np.testing.assert_array_equal(TOOLS['serial_solve'](a, b), [[2.], [1.]])
    np.testing.assert_array_equal(TOOLS['serial_product'](a, [[2.], [1.]]), b)
    # Fixed order intentionally retains the cancellation loss in this sequence.
    np.testing.assert_array_equal(TOOLS['serial_product']([[1e16, 1., -1e16]], [[1.], [1.], [1.]]), [[0.]])
