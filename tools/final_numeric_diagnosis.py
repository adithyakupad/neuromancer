"""Read-only numerical diagnostics. Neither acceptance rules nor package algorithms."""
import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import runpy
import subprocess
import sys

import numpy as np
import scipy


def difference(reference, observed):
    """Byte equality and finite float64 error, preserving signed-zero differences."""
    reference = np.asarray(reference)
    observed = np.asarray(observed)
    result = dict(shape=list(reference.shape), observed_shape=list(observed.shape),
                  dtype=str(reference.dtype), observed_dtype=str(observed.dtype),
                  exact=False)
    if reference.shape != observed.shape or reference.dtype != observed.dtype:
        return result
    result['exact'] = reference.tobytes() == observed.tobytes()
    if not np.issubdtype(reference.dtype, np.number):
        return result
    a = reference.astype(np.float64)
    b = observed.astype(np.float64)
    finite = np.isfinite(a) & np.isfinite(b)
    absolute = np.abs(a[finite] - b[finite])
    nonzero = np.abs(a[finite]) > 0
    result.update(max_absolute_error=float(absolute.max(initial=0)),
                  max_relative_error_nonzero=float((absolute[nonzero] / np.abs(a[finite][nonzero])).max(initial=0)),
                  zero_reference_nonzero_observed=int(np.count_nonzero((a[finite] == 0) & (b[finite] != 0))),
                  nonfinite_pairs=int(np.count_nonzero(~finite)),
                  semantic_equal=bool(np.array_equal(reference, observed, equal_nan=True)))
    result['relative_error_unbounded'] = result['zero_reference_nonzero_observed'] > 0
    result['max_relative_error'] = (None if result['relative_error_unbounded'] else
                                    result['max_relative_error_nonzero'])
    if reference.dtype == np.float64:
        # Ordered unsigned encodings avoid signed-int overflow across zero.
        x = np.where(a[finite] == 0, 0., a[finite]).view(np.uint64)
        y = np.where(b[finite] == 0, 0., b[finite]).view(np.uint64)
        sign = np.uint64(1 << 63)
        x = np.where(x & sign, ~x, x | sign)
        y = np.where(y & sign, ~y, y | sign)
        distance = np.maximum(x, y) - np.minimum(x, y)
        result.update(max_ulp_distance=int(distance.max(initial=0)),
                      changed_finite_values=int(np.count_nonzero(distance)))
    return result


def serial_product(a, b):
    """Explicit binary64 multiply then add in ascending index order, no BLAS."""
    left = np.asarray(a, dtype=float).tolist()
    right = np.asarray(b, dtype=float).T.tolist()
    result = []
    for row in left:
        output = []
        for column in right:
            total = 0.
            for x, y in zip(row, column, strict=True):
                product = x * y
                total = total + product
            output.append(total)
        result.append(output)
    return np.asarray(result)


def serial_solve(a, b):
    """Diagnostic Gaussian elimination with first-largest partial-pivot ties."""
    matrix = np.asarray(a, dtype=float).tolist()
    rhs = np.asarray(b, dtype=float).tolist()
    n = len(matrix)
    columns = len(rhs[0])
    for k in range(n):
        pivot = max(range(k, n), key=lambda row: abs(matrix[row][k]))
        if matrix[pivot][k] == 0:
            raise ArithmeticError('Singular diagnostic system')
        matrix[k], matrix[pivot] = matrix[pivot], matrix[k]
        rhs[k], rhs[pivot] = rhs[pivot], rhs[k]
        for i in range(k + 1, n):
            factor = matrix[i][k] / matrix[k][k]
            matrix[i][k] = 0.
            for j in range(k + 1, n):
                product = factor * matrix[k][j]
                matrix[i][j] = matrix[i][j] - product
            for j in range(columns):
                product = factor * rhs[k][j]
                rhs[i][j] = rhs[i][j] - product
    solution = [[0.] * columns for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(columns):
            total = rhs[i][j]
            for k in range(i + 1, n):
                product = matrix[i][k] * solution[k][j]
                total = total - product
            solution[i][j] = total / matrix[i][i]
    return np.asarray(solution)


def environment(output):
    config = io.StringIO()
    with contextlib.redirect_stdout(config):
        np.show_config()
        np.show_runtime()
        scipy.show_config()
    (output/'numerical-runtime.txt').write_text(config.getvalue())
    libraries = []
    if sys.platform == 'darwin':
        import ctypes
        library = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
        library._dyld_image_count.restype = ctypes.c_uint32
        library._dyld_get_image_name.argtypes = [ctypes.c_uint32]
        library._dyld_get_image_name.restype = ctypes.c_char_p
        libraries = [library._dyld_get_image_name(index).decode()
                     for index in range(library._dyld_image_count())]
    elif Path('/proc/self/maps').exists():
        libraries = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                            if '/' in line})
    selected = [name for name in libraries if any(word in name.lower()
                for word in ('blas', 'lapack', 'accelerate', 'veclib', 'multiarray', '_umath_linalg'))]
    binaries = {}
    wheels = {}
    for module in (np, scipy):
        distribution = importlib.metadata.distribution(module.__name__)
        wheels[module.__name__] = distribution.read_text('WHEEL')
        base = Path(module.__file__).parent
        for path in sorted(base.rglob('*.so')):
            if any(word in path.name for word in ('multiarray', '_umath_linalg', '_flapack', '_fblas')):
                binaries[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in selected:
        if Path(name).is_file():
            binaries[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    return dict(platform=platform.platform(), processor=platform.processor(), python=sys.version,
                executable=sys.executable, numpy=np.__version__, scipy=scipy.__version__,
                numpy_path=np.__file__, scipy_path=scipy.__file__, loaded_numerical_libraries=selected,
                binary_sha256=binaries, wheel_metadata=wheels, thread_requests={name: os.environ.get(name) for name in
                ('VECLIB_MAXIMUM_THREADS', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')},
                actual_threads='Not established unless the runtime report independently supplies a pool count')


def probe(output):
    output.mkdir(parents=True, exist_ok=False)
    reference_path = Path('reports/engineering/evidence/m017/golden_final')
    saved = np.load(reference_path/'outputs.npz')
    record = json.loads((reference_path/'records.json').read_text())['initial']
    design = saved['initial_design']
    targets = saved['initial_targets']
    penalty = len(design) * .1 * np.diag(np.r_[0., np.ones(40)])
    gram = design.T @ design + penalty
    rhs = design.T @ targets
    serial_gram = serial_product(design.T, design) + penalty
    serial_rhs = serial_product(design.T, targets)
    native_theta = np.linalg.solve(gram, rhs)
    native_serial_theta = np.linalg.solve(serial_gram, serial_rhs)
    serial_theta = serial_solve(serial_gram, serial_rhs)
    reference_theta = saved['initial_theta']
    residual = gram @ native_theta - rhs
    denominator = np.linalg.norm(gram, np.inf)*np.linalg.norm(native_theta, np.inf)+np.linalg.norm(rhs, np.inf)
    # Fix the archived initial state to isolate one RLS arithmetic step from fitting drift.
    z = design[-1]
    p = saved['initial_information_inverse']
    gain = p @ z / (.999 + z @ p @ z)
    updated_theta = reference_theta + np.outer(gain, targets[-1] - z @ reference_theta)
    updated_p = (p - np.outer(gain, z @ p)) / .999
    updated_p = (updated_p + updated_p.T) / 2
    from neuromancer._brian import realization
    from neuromancer.substrate import Config
    import brian2 as brian
    realization_data = realization(Config())
    weights = realization_data['weight_pA']
    returned_weights = np.asarray((weights * brian.pA) / brian.pA)
    arrays = dict(gram=gram, rhs=rhs, serial_gram=serial_gram, serial_rhs=serial_rhs,
                  native_theta=native_theta, native_serial_theta=native_serial_theta,
                  serial_theta=serial_theta, native_p=np.linalg.inv(gram),
                  fixed_state_predictions=design @ reference_theta,
                  serial_fixed_state_predictions=serial_product(design, reference_theta),
                  updated_theta=updated_theta, updated_p=updated_p,
                  generated_weights=weights, returned_weights=returned_weights)
    # Reuse the exact original synthetic fixture, without neural acquisition.
    fixture = runpy.run_path('tests/test_predictive.py')['fixture']()
    initial = fixture[0]
    arrays['fixture_theta'] = np.asarray(initial.record['coef'])
    arrays['fixture_design'] = fixture[1]
    from neuromancer.predictive_planner import plan
    native_plan = plan(record, native_theta, np.zeros((9, 4)), 9., 51_000_000, clock=lambda: 0)
    fixed_plan = plan(record, reference_theta, np.zeros((9, 4)), 9., 51_000_000, clock=lambda: 0)
    arrays['native_plan_cost'] = native_plan['cost']
    arrays['archived_theta_plan_cost'] = fixed_plan['cost']
    result = dict(environment=environment(output), conditioning=dict(
        design_rank=int(np.linalg.matrix_rank(design)), columns=design.shape[1],
        unregularized_condition=None, regularized_gram_condition=float(np.linalg.cond(gram)),
        ridge_backward_residual_inf=float(np.linalg.norm(residual, np.inf)/denominator),
        input_history_reduced_condition=record['diagnostics']['reduced_condition']),
        comparisons=dict(native_vs_archived=difference(reference_theta, native_theta),
                         serial_vs_archived=difference(reference_theta, serial_theta),
                         native_vs_serial_gram=difference(serial_gram, gram),
                         native_vs_serial_rhs=difference(serial_rhs, rhs),
                         native_solver_on_serial_vs_serial_solver=difference(serial_theta, native_serial_theta),
                         fixed_predictions_vs_serial=difference(arrays['serial_fixed_state_predictions'], arrays['fixed_state_predictions']),
                         unit_roundtrip=difference(weights, returned_weights)),
        native_planner_chosen=native_plan['chosen'], fixed_state_planner_chosen=fixed_plan['chosen'],
        fixture_source_sha256=hashlib.sha256(Path('tests/test_predictive.py').read_bytes()).hexdigest(),
        source_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    np.savez_compressed(output/'operations.npz', **arrays)
    (output/'probe.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    probe(arguments.output)
