"""Rational audit of the first different native operation in an M030 capture."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.m029_parallel import ARCHIVE, manifest, read
from tools.m030_trace import first_difference
from neuromancer.supervisor import atomic_json


def bit_strings(value):
    return [f'0x{word:016x}' for word in np.asarray(value, dtype=np.float64).view(np.uint64).ravel()]


def dot_oracle(a, b, actual):
    terms = [Fraction(float(x))*Fraction(float(y)) for x, y in zip(a, b, strict=True)]
    exact = sum(terms)
    unit = Fraction(1, 2**53)
    factor = len(terms)*unit/(1-len(terms)*unit)
    envelope = factor * sum(abs(term) for term in terms)
    error = abs(Fraction(actual)-exact)
    return dict(left=list(map(float, a)), right=list(map(float, b)),
        left_bits=bit_strings(a), right_bits=bit_strings(b), exact_numerator=str(exact.numerator),
        exact_denominator=str(exact.denominator), rounded_reference=float(exact),
        absolute_error=float(error), dot_error_bound=float(envelope), contained=error <= envelope)


def operand_audit(root):
    result = []
    for row in read(root/'first-divergence.json')['branches']:
        name, witness = row['first_matmul'], row['first_operation_operands']
        if name is None:
            result.append(dict(branch=row['branch'], operation=None,
                               first_native_update=row['first_native_update']))
            continue
        diff = row['differences'][name]
        step, *coordinate = diff['index']
        expression = name.split(' ', 1)[1]
        left, right = [], []
        if expression == 'z @ self.p':
            left = witness['z']
            right = [np.asarray(p)[:, coordinate[0]] for p in witness['previous_covariance']]
        elif expression == 'self.p @ z':
            left = [np.asarray(p)[coordinate[0]] for p in witness['previous_covariance']]
            right = witness['z']
        elif expression == 'z @ self.theta':
            left = witness['z']
            right = [np.asarray(p)[:, coordinate[0]] for p in witness['previous_theta']]
        elif expression == 'z @ self.p @ z':
            index = manifest().index(row['branch'])
            for workers in (1, 2):
                trace = root/f'workers-{workers}'/f'trace-{index:02}'
                key = name.split(' ', 1)[0]+' z @ self.p'
                left.append(np.load(trace/read(trace/'index.json')['trace'][key], mmap_mode='r')[step])
            right = witness['z']
        else:
            # These are post-update guard products. They cannot establish a
            # first state cause unless the computed coefficient operands agree.
            result.append(dict(branch=row['branch'], operation=expression, index=step,
                               unresolved='Post-update guard product has no independent theta witness'))
            continue
        comparisons = [dot_oracle(a, b, actual)
                       for a, b, actual in zip(left, right, diff['values'], strict=True)]
        same = all(first_difference(np.asarray(v[0]), np.asarray(v[1])) is None for v in (left, right))
        before_same = all(first_difference(np.asarray(v[0]), np.asarray(v[1])) is None for v in
                          (witness['previous_theta'], witness['previous_covariance'], witness['x'], witness['y'], witness['z']))
        result.append(dict(branch=row['branch'], operation=expression, index=step,
            element=coordinate, output=diff, same_operands=same, same_previous_state_and_inputs=before_same,
            addresses_mod64=witness[name+' addresses_mod64'], rational=comparisons))
    return result


def state_boundaries(root):
    evidence = []
    for row in read(root/'first-divergence.json')['branches']:
        identity, step = row['branch'], row['first_native_update']
        if step is None:
            continue
        index = manifest().index(identity)
        arrays = []
        previous = []
        for workers in (1, 2):
            path = root/f'workers-{workers}'/f'trace-{index:02}'
            data = {name: np.load(path/filename, mmap_mode='r') for name, filename
                    in read(path/'index.json')['trace'].items()}
            arrays.append(data)
            if step:
                previous.append({name: data[name][step-1] for name in ('theta', 'covariance', 'bias')})
            else:
                with np.load(path/'initial.npz') as initial:
                    previous.append(dict(initial))
        n, rep, _ = identity
        ym = read(ARCHIVE/f'n{n}_r{rep}'/'initial.json')['record']['output_mean']
        products, states = [], []
        for data, before in zip(arrays, previous, strict=True):
            left, right = data['9:29 z @ self.p'][step], data['z'][step]
            quadratic = float(data['9:29 z @ self.p @ z'][step])
            denominator = .999+quadratic
            gain = data['11:17 self.p @ z'][step]/denominator
            residual = (data['y'][step]-ym)-data['11:71 z @ self.theta'][step]
            theta = before['theta']+np.outer(gain, residual)
            p = (before['covariance']-np.outer(gain, data['12:36 z @ self.p'][step]))/.999
            p = (p+p.T)/2
            states.append(dict(denominator=denominator, denominator_bits=bit_strings(denominator),
                               reconstructed_theta_exact=first_difference(theta, data['theta'][step]) is None,
                               reconstructed_covariance_exact=first_difference(p, data['covariance'][step]) is None))
            products.append(dict(quadratic=quadratic, quadratic_bits=bit_strings(quadratic),
                addresses_mod64=data['9:29 z @ self.p @ z addresses_mod64'][step].tolist(),
                **dot_oracle(left, right, quadratic)))
        differences = {name: difference for name in arrays[0] if arrays[0][name].dtype == np.float64
                       if (difference := first_difference(arrays[0][name][step], arrays[1][name][step]))}
        evidence.append(dict(branch=identity, step=step,
            previous_state_exact=all(first_difference(previous[0][name], previous[1][name]) is None for name in previous[0]),
            only_input_product_difference=set(differences)-{'theta', 'covariance', 'bias'} == {'9:29 z @ self.p @ z'},
            differences=differences, quadratic_products=products, update_reconstruction=states))
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    atomic_json(args.output, dict(results=operand_audit(args.trace),
                state_boundaries=state_boundaries(args.trace), qualification=False))
