"""Bounded diagnostic replay of the M029 worker-count comparison."""
import argparse
import ast
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import m028_backend, m029_parallel as scheduler
from neuromancer.supervisor import atomic_json

TARGETS = ((0, 47, 'LOSS_RLS-MPC'), (1, 47, 'STATIC_RLS-MPC'), (1, 47, 'LOSS_RLS-MPC'))
BIN_COUNT = 3200


def native_update_probe(native, observe):
    """Compile only the original method with its @ operators observed."""
    source = textwrap.dedent(inspect.getsource(native))
    operations = {}

    class Observe(ast.NodeTransformer):
        def visit_BinOp(self, node):
            expression = ast.unparse(node)
            self.generic_visit(node)
            if isinstance(node.op, ast.MatMult):
                label = f'{node.lineno}:{node.col_offset} {expression}'
                operations[label] = expression
                return ast.copy_location(ast.Call(ast.Name('observe', ast.Load()),
                    [ast.Constant(label), node.left, node.right], []), node)
            return node

    tree = Observe().visit(ast.parse(source))
    namespace = {**native.__globals__, 'observe': observe}
    exec(compile(ast.fix_missing_locations(tree), '<M030 observed native update>', 'exec'), namespace)
    return namespace[native.__name__], operations, hashlib.sha256(source.encode()).hexdigest()


def proof_operands(kernel, state, theta, covariance, actual):
    """Reconstruct the bound operation tree beside the original compiled call."""
    s, rs = state.information.center, state.information.radius
    h, rh = state.rhs.center, state.rhs.radius
    product = s @ theta
    uncertain = kernel.positive_product(rs, abs(theta))
    absolute = kernel.positive_product(abs(s), abs(theta))
    g = kernel.gamma(s.shape[1])
    u = np.finfo(float).eps / 2
    up = kernel.upward
    radius = up(up(uncertain))
    radius = up(radius + up((2*g) * absolute))
    value = h-product
    radius = up(up(rh+radius) + up((2*u/(1-u))*abs(value)))
    magnitude = up(abs(value)+radius)
    residual = magnitude.max(axis=0)
    coefficient = up(actual['inverse_upper']*residual)
    return dict(s=s, rs=rs, h=h, rh=rh, theta=theta, covariance=covariance,
                center_product=product, uncertain=uncertain, absolute_product=absolute,
                residual_center=value, residual_rounding_radius=radius, magnitude=magnitude,
                reduced_residual=residual, inverse_upper=np.asarray(actual['inverse_upper']),
                reconstructed_coefficient=coefficient,
                actual_residual=actual['residual_by_output'], actual_coefficient=actual['coefficient_radius'])


def capture(output, branch, source):
    from neuromancer.predictive import FIRModel

    branch = tuple(branch)
    if branch not in TARGETS:
        return scheduler.worker(output, branch, source)
    sidecar = output.with_name(output.name.replace('branch-', 'trace-'))
    sidecar.mkdir()
    trace = {}
    position = 0
    proof_calls = 0

    def record(name, value):
        value = np.asarray(value)
        if name not in trace:
            trace[name] = np.lib.format.open_memmap(
                sidecar/f'{len(trace):02}.npy', mode='w+', dtype=value.dtype,
                shape=(BIN_COUNT, *value.shape))
        trace[name][position] = value

    def observe(label, left, right):
        result = left @ right
        record(label, result)
        record(label+' addresses_mod64', np.array(
            [np.asarray(v).ctypes.data % 64 for v in (left, right, result)], dtype=np.uint8))
        return result

    update, operators, update_sha = native_update_probe(FIRModel.update, observe)
    original_bounds, original_driver = m028_backend.bounds, m028_backend.driver

    def bounds(kernel):
        module = original_bounds(kernel)
        # Only the original M028 kernel is used for the historical radius site.
        if branch == TARGETS[1] and 'M029_KERNEL_DIR' not in os.environ:
            class ProofObserved(module.InformationCertificate):
                def state(self, theta, covariance):
                    nonlocal proof_calls
                    result = super().state(theta, covariance)
                    if self.updates == 1250:
                        np.savez_compressed(sidecar/f'proof-{proof_calls}.npz',
                            **proof_operands(kernel, self, theta, covariance, result))
                        proof_calls += 1
                    return result
            module.InformationCertificate = ProofObserved
        return module

    def driver(module):
        replay = original_driver(module)
        checked = replay._checked_model_type

        class Observed(checked):
            def standardized(self, x):
                value = super().standardized(x)
                record('z', value)
                return value

            def update(self, x, y, valid=True):
                nonlocal position
                record('x', x)
                record('y', y)
                if position == 0:
                    np.savez(sidecar/'initial.npz', theta=self.theta, covariance=self.p, bias=self.bias_p)
                super().update(x, y, valid)
                record('theta', self.theta)
                record('covariance', self.p)
                record('bias', self.bias_p)
                position += 1

        replay._checked_model_type = Observed
        return replay

    # A private subclass lets CheckedModel retain its denominator guard and
    # call the observed copy. The installed production module is untouched.
    class ObservedNative(FIRModel):
        pass

    ObservedNative.update = update

    def observed_driver(module):
        # Bind the already source-checked driver to the diagnostic class in its
        # isolated construction only. Restore the package binding immediately.
        from neuromancer import predictive
        original = predictive.FIRModel
        try:
            predictive.FIRModel = ObservedNative
            return driver(module)
        finally:
            predictive.FIRModel = original

    m028_backend.bounds, m028_backend.driver = bounds, observed_driver
    try:
        code = scheduler.worker(output, branch, source)
    finally:
        m028_backend.bounds, m028_backend.driver = original_bounds, original_driver
        for array in trace.values():
            array.flush()
        atomic_json(sidecar/'index.json', dict(branch=list(branch), source=source, updates=position,
            operators=operators, native_update_source_sha256=update_sha,
            trace={name: f'{i:02}.npy' for i, name in enumerate(trace)},
            proof_calls=proof_calls, files={file.name: scheduler.sha(file)
            for file in sorted(sidecar.iterdir()) if file.is_file()}))
    return code


def first_difference(a, b):
    if a.shape != b.shape or a.dtype != b.dtype:
        raise ValueError('Mismatched trace array schema')
    left, right = a.view(np.uint64).ravel(), b.view(np.uint64).ravel()
    different = np.flatnonzero(left != right)
    if not len(different):
        return None
    idx = int(different[0])
    coordinate = tuple(int(i) for i in np.unravel_index(idx, a.shape))
    return dict(index=list(coordinate), values=[float(a[coordinate]), float(b[coordinate])],
                bits=[f'0x{left[idx]:016x}', f'0x{right[idx]:016x}'])


def compare(root):
    reports = []
    for i, branch in enumerate(scheduler.manifest()[:8]):
        if tuple(branch) not in TARGETS:
            continue
        paths = [root/f'workers-{n}'/f'trace-{i:02}' for n in (1, 2)]
        records = [scheduler.read(path/'index.json') for path in paths]
        if any(row['branch'] != branch or row['updates'] != BIN_COUNT for row in records):
            raise ValueError('Incomplete or misidentified operand trace')
        for path, row in zip(paths, records, strict=True):
            if any(scheduler.sha(path/name) != sha for name, sha in row['files'].items()):
                raise ValueError('Operand trace integrity failure')
        initial = [np.load(path/'initial.npz') for path in paths]
        inputs = {key: first_difference(*(z[key] for z in initial)) for key in initial[0].files}
        arrays = [{key: np.load(path/name, mmap_mode='r')
                   for key, name in row['trace'].items()} for path, row in zip(paths, records, strict=True)]
        if arrays[0].keys() != arrays[1].keys():
            raise ValueError('Trace operation coverage differs')
        differences = {key: first_difference(arrays[0][key], arrays[1][key]) for key in arrays[0]
                       if arrays[0][key].dtype == np.float64}
        native = [differences[k] for k in ('theta', 'covariance', 'bias') if differences[k]]
        step = min((row['index'][0] for row in native), default=None)
        operations = [key for key in records[0]['operators'] if key in differences and differences[key]]
        first_op = min(operations, key=lambda key: (differences[key]['index'][0],
                      list(arrays[0]).index(key)), default=None)
        witness = {}
        if first_op is not None:
            at = differences[first_op]['index'][0]
            for name in ('x', 'y', 'z', first_op, first_op+' addresses_mod64'):
                witness[name] = [a[name][at].tolist() for a in arrays]
            witness['previous_theta'] = [(a['theta'][at-1] if at else old['theta']).tolist()
                                        for a, old in zip(arrays, initial, strict=True)]
            witness['previous_covariance'] = [(a['covariance'][at-1] if at else old['covariance']).tolist()
                                             for a, old in zip(arrays, initial, strict=True)]
        proofs = []
        for left, right in zip(sorted(paths[0].glob('proof-*.npz')), sorted(paths[1].glob('proof-*.npz')), strict=True):
            with np.load(left) as a, np.load(right) as b:
                proofs.append(dict(call=left.name,
                    matches_compiled=[v['reconstructed_coefficient'].tobytes() == v['actual_coefficient'].tobytes()
                                      for v in (a,b)],
                    differences={k: row for k in a.files if (row := first_difference(a[k], b[k]))}))
        reports.append(dict(branch=branch, initial_differences=inputs, first_native_update=step,
             first_matmul=first_op, differences={k: v for k,v in differences.items() if v},
             first_operation_operands=witness, proof_calls=proofs))
    atomic_json(root/'first-divergence.json', dict(branches=reports, qualification=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['worker', 'coordinate', 'compare', 'pair'])
    parser.add_argument('output', type=lambda path: Path(path).resolve())
    parser.add_argument('first', nargs='?')
    parser.add_argument('second', nargs='?')
    args = parser.parse_args()
    if args.mode == 'worker':
        sys.exit(capture(args.output, json.loads(args.first), args.second))
    if args.mode == 'compare':
        compare(args.output)
    else:
        scheduler.__file__ = __file__
        if args.mode == 'coordinate':
            sys.exit(scheduler.coordinate(args.output, int(args.first), int(args.second)))
        args.output.mkdir(parents=True, exist_ok=False)
        codes = [scheduler.launch(args.output/f'workers-{n}', n, 8) for n in (1, 2)]
        if any(codes):
            sys.exit(1)
        compare(args.output)
