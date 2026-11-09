"""Portable certificates and explicit coverage of the remaining saved families."""
import argparse
import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.m029_fits import Ball, arx_fits, endpoints, exact, initial_fit, members, require
from tools.m029_forecasts import controller_and_feedback, fir_models, graph_weights, online_models, planner_fixtures
from tools.m027_spectral_bounds import condition_interval
from tools.portable_numeric_verification import CertificateFailure

GOLDEN = Path('reports/engineering/evidence/m017/golden_final')
RESEARCH = Path('reports/research/evidence')
V1 = Path('reports/evidence/v1_finish')


def read(path):
    return json.loads(path.read_text())


def archived_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return dict(archive)


def v1_outputs(output, execute):
    root = output/'v1'
    source = V1/'m005b'
    execute([sys.executable, '-m', 'neuromancer.m005b_analysis', str(source/'primary'), str(root)], 'v1-analysis')
    compared = {}
    for name in ('trial_metrics.csv', 'timecourses.csv', 'network_qualification.csv', 'summary.json'):
        observed = (root/name).read_bytes()
        require(observed == (source/'analysis_primary'/name).read_bytes(), 'Canonical V1 differs: '+name)
        compared[name] = hashlib.sha256(observed).hexdigest()
    execute([sys.executable, str(V1/'verify_metrics.py'), str(source/'primary'), str(root),
             str(output/'v1-statistics.json')], 'v1-statistics')
    return dict(exact_outputs=compared, independent_statistics=read(output/'v1-statistics.json'))


def study_discrete(deadline):
    source = V1/'m005b/primary'
    bins = events = branches = 0
    for network, replicate in read(source/'provenance.json')['jobs']:
        folder = source/f'n{network}_r{replicate}'
        trial = read(folder/'trial.json')
        require(trial['status'] == 'complete' and [trial['network'], trial['replicate']] == [network, replicate],
                'Saved study trial identity differs')
        with np.load(folder/'initial.npz') as init:
            prior = init['history'][-1]
        for branch in trial['branches']:
            deadline.check()
            data = archived_npz(folder/(branch['name']+'.npz'))
            n = branch['bins']
            currents = data['delivered']
            exact(currents, data['requested'], 'V1 requested and delivered current')
            require(currents.shape == (n, 4) and (currents >= 0).all() and (currents <= 120).all()
                    and (currents.sum(1) <= 240).all() and not currents[:, 1::2].any()
                    and np.array_equal(currents[:, 0], currents[:, 2])
                    and (abs(np.diff(np.vstack([prior, currents]), axis=0)) <= 30).all(),
                    'V1 exact constraint check failed')
            starts = 51_000_000+20_000*np.arange(n)
            exact(np.c_[starts, starts+20000, starts+20000], data['time_us'], 'V1 observation times')
            require(data['valid'].all() and (data['coverage_us'] == 20000).all(), 'V1 observation validity changed')
            offsets = data['event_offset']
            channels = data['event_channel']
            times = data['event_time_us']
            require(len(offsets) == n+1 and offsets[0] == 0 and offsets[-1] == len(channels) == len(times)
                    and (np.diff(offsets) >= 0).all() and ((0 <= channels) & (channels < 20)).all(),
                    'V1 event extent or channel differs')
            owners = np.repeat(np.arange(n), np.diff(offsets))
            require(((starts[owners] <= times) & (times < starts[owners]+20000)).all(),
                    'V1 event is outside its original observation bin')
            counts = np.bincount(owners*20+channels, minlength=n*20).reshape(n, 20)
            exact(data['counts'], counts.astype(data['counts'].dtype), 'V1 event-derived observation counts')
            branches += 1
            bins += n
            events += len(times)
    return dict(branches=branches, bins=bins, archived_events=events)


def m013(output, execute):
    source = RESEARCH/'m013/pilot_typed'
    scratch = output/'m013'
    shutil.copytree(source, scratch)
    execute([sys.executable, 'scripts/m013_analyze.py', str(scratch)], 'm013')
    old, new = (read(path/'independent_analysis.json') for path in (source, scratch))
    expected_rows, actual_rows = old.pop('rows'), new.pop('rows')
    require(old == new, 'M013 scientific summary differs')
    intervals = []
    for reference, candidate in zip(expected_rows, actual_rows, strict=True):
        prior = reference.pop('probe_design_condition')
        observed = candidate.pop('probe_design_condition')
        require(reference == candidate, 'M013 discrete or scientific row differs')
        with np.load(source/f"{reference['network']}_{reference['condition']}.npz") as archive:
            design = np.column_stack([np.ones(len(archive['x_probe'])),
                                      (archive['x_probe']-archive['mean'])/archive['scale']])
        lower, upper, spectral = condition_interval(design)
        require(lower <= prior <= upper and lower <= observed <= upper, 'M013 condition escaped enclosure')
        intervals.append(dict(network=reference['network'], condition=reference['condition'],
                              interval=[lower, upper], absolute_error=spectral['absolute_error']))
    return dict(rows=len(intervals), conditions=intervals, scientific_decision=old['scientific_decision'])


def exact_reduction_at_half(row, coefficient):
    """Sufficient exactness proof for a binary64 dot at its classification threshold."""
    terms = [Fraction(float(a))*Fraction(float(b)) for a, b in zip(row, coefficient, strict=True)]
    scale = max(term.denominator for term in terms)
    integers = [term.numerator*(scale//term.denominator) for term in terms]
    # A common power-of-two lattice with <=53 significant bits for every
    # possible partial sum makes products and arbitrary accumulation exact.
    return (scale <= 2**1022 and sum(map(abs, integers)).bit_length() <= 53
            and 2*sum(integers) == scale)


def m014(output):
    source = RESEARCH/'m014/pilot'
    scratch = output/'m014'
    shutil.copytree(source, scratch)
    statistics = []

    def certify_predictions(design, coefficient, expected):
        native = design@coefficient
        result = Ball(design).product(Ball(coefficient))
        members(result, 'M014 readout predictions', expected, native)
        exact(expected >= .5, native >= .5, 'M014 classification')
        lower, upper = endpoints(result)
        unresolved = np.flatnonzero((lower < .5) & (upper >= .5))
        require(all(exact_reduction_at_half(design[i], coefficient) for i in unresolved),
                'M014 interval crosses a classification guard')
        statistics.append(dict(predictions=len(native), radius=float(result.radius.max()),
                               exact_half_certificates=len(unresolved)))

    # Keep the original analysis and every other assertion. Replace only the
    # two exact floating dot comparisons that already have known BLAS drift.
    path = Path('scripts/m014_analyze.py')
    tree = ast.parse(path.read_text(), filename=str(path))
    targets = {
        "np.testing.assert_allclose(design @ archive['coefficients'], archive['predictions'], rtol=0, atol=0)",
        "np.testing.assert_array_equal(design @ archive['coefficients'], archive['predictions'])",
    }
    replaced = set()

    class ReadoutAudit(ast.NodeTransformer):
        def visit_Expr(self, node):
            expression = ast.unparse(node.value)
            if expression not in targets:
                return node
            if expression in replaced:
                raise CertificateFailure('Duplicated M014 assertion')
            replaced.add(expression)
            return ast.copy_location(ast.parse(
                "certify_predictions(design, archive['coefficients'], archive['predictions'])").body[0], node)

    tree = ReadoutAudit().visit(tree)
    require(replaced == targets, 'Original M014 assertion boundary differs')
    argv = sys.argv
    try:
        sys.argv = [str(path), str(scratch)]
        exec(compile(ast.fix_missing_locations(tree), str(path), 'exec'), {'certify_predictions': certify_predictions})
    finally:
        sys.argv = argv
    archived = read(source/'independent_analysis.json')
    require(archived == read(scratch/'independent_analysis.json'), 'M014 scientific summary differs')
    require(len(statistics) == archived['prediction_archives_verified']+archived['lag_archives_verified'],
            'Incomplete M014 prediction audit')
    return dict(certificates=statistics, scientific_decision=archived['scientific_decision'])


def m015(output, deadline):
    source = RESEARCH/'m015'
    scratch = output/'m015'
    shutil.copytree(source/'cross', scratch/'cross')
    verifier = runpy.run_path('scripts/m015_verify.py')
    replay = runpy.run_path('scripts/m015_cross_simulator.py')['scalar_simulator']
    result = verifier['verify_cross'](scratch)
    arrays = sorted((scratch/'cross').glob('*.npz'))
    require(len(arrays) == 8, 'M015 comparison case count differs')
    for path in arrays:
        deadline.check()
        data = archived_npz(path)
        spikes, current = replay(data['drive'])
        exact(data['reference_spikes'], spikes, path.name+' scalar spike identities')
        exact(data['reference_current'], current, path.name+' scalar current trace')
    return {**result, 'scalar_trajectory_replays': len(arrays),
            'cue_access': 'FAIL', 'retention': 'NOT RUN'}


def m016(output, execute, sdk_python):
    require(sdk_python is not None, 'Pinned SDK archive reader unavailable')
    source = Path('reports/engineering/evidence/m016/final_matrix')
    scratch = output/'m016'
    shutil.copytree(source, scratch)
    shutil.copy2(source.with_name(source.name+'_descendants.json'), scratch.with_name('m016_descendants.json'))
    execute([sdk_python, 'scripts/m017_sdk_verify.py', str(scratch)], 'm016-saved-readonly')
    result = read(output/'m016_verification.json')
    pi, baseline = (result['cases'][name]['absolute_tracking_error'] for name in ('PI', 'FROZEN'))
    require((pi, baseline) == (1.5, 1.), 'M016 tracking result differs')
    return dict(recording_cases=9, paired_receipts=result['all_paired_receipts'],
                PI=pi, no_pulse=baseline, scientific_decision='FAIL')


def golden(reference, candidate, stage, deadline):
    old, new = (archived_npz(path/'outputs.npz') for path in (reference, candidate))
    records, new_records = (read(path/'records.json') for path in (reference, candidate))
    require(len(old) == 102 and old.keys() == new.keys() and records.keys() == new_records.keys(),
            'Original golden schema differs')
    for name in old:
        require(old[name].dtype == new[name].dtype and old[name].shape == new[name].shape,
                f'Golden dtype or shape differs: {name}')

    fixture = runpy.run_path('tests/test_predictive.py')['fixture']()
    array_coverage, record_coverage = set(), set()
    def check(name, action, arrays, keys):
        if stage(name, action):
            array_coverage.update(arrays)
            record_coverage.update(keys)

    check('initial_fit', lambda: initial_fit(fixture, old, records, new, new_records),
          [key for key in old if key.startswith('initial_')], ['initial'])
    check('fir_forecasts', lambda: fir_models(fixture, old, new, records, new_records, deadline),
          [f'{kind}_{field}' for kind in ('FIXED', 'RLS', 'BIAS') for field in ('predictions', 'theta', 'p')],
          ['FIXED', 'RLS', 'BIAS'])
    check('online_fir', lambda: online_models(old, new, records, new_records, deadline),
          [key for key in old if '_online_' in key], [key for key in records if key.endswith('_online')])
    predictors = [f'{family}{lags}' for family in ('AR', 'ARX', 'SHUFFLED') for lags in (1, 4)]
    check('arx_fits_and_forecasts', lambda: arx_fits(old, records, new, new_records, deadline),
          [p+'_prediction' for p in predictors], predictors)
    check('planner', lambda: planner_fixtures(fixture, old, new, records, new_records, deadline),
          [key for key in old if key.startswith('planner_')], [key for key in records if key.startswith('planner_')])
    check('controller_feedback', lambda: controller_and_feedback(fixture, old, new, records, new_records, deadline),
          [key for key in old if '_controller_' in key or key in
           ('FIXED_actions', 'RLS_actions', 'feedback_forecasts', 'feedback_coefficients')],
          ['FIXED_events', 'RLS_events', 'feedback'])
    check('graph_rounding', lambda: graph_weights(old['dag_edges'], new['dag_edges']), ['dag_edges'], ['dag_edges'])

    exact_arrays, exact_records, unexplained_arrays, unexplained_records = [], [], [], []
    for key in old:
        if old[key].tobytes() == new[key].tobytes():
            exact_arrays.append(key)
        elif key not in array_coverage:
            unexplained_arrays.append(key)
    for key in records:
        if records[key] == new_records[key]:
            exact_records.append(key)
        elif key not in record_coverage:
            unexplained_records.append(key)
    return dict(exact_arrays=exact_arrays, exact_records=exact_records,
                certified_arrays=sorted(array_coverage), certified_records=sorted(record_coverage),
                uncovered_arrays=unexplained_arrays, uncovered_records=unexplained_records)


def run(output, captured, sdk_python):
    from neuromancer.supervisor import Deadline, atomic_json
    from scripts.m017_reproduce import verify_history

    deadline = Deadline.from_environment()
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    started = time.monotonic()

    def execute(command, name):
        deadline.check()
        with (output/(name+'.log')).open('wb') as stream:
            subprocess.run(command, check=True, stdout=stream, stderr=subprocess.STDOUT)

    def stage(name, function):
        deadline.check()
        began = time.monotonic()
        try:
            evidence = function()
        except (ArithmeticError, AssertionError, ValueError, KeyError, OSError, RuntimeError,
                subprocess.CalledProcessError, np.linalg.LinAlgError) as error:
            results[name] = dict(passed=False, error=repr(error))
        else:
            results[name] = dict(passed=True, evidence=evidence)
        results[name]['wall_s'] = time.monotonic()-began
        atomic_json(output/'progress.json', dict(stages=results, release_qualified=False))
        return results[name]['passed']

    stage('protected_paths', lambda: dict(paths=verify_history()))
    candidate = captured or output/'golden'
    if captured is not None or stage('golden_capture', lambda: execute(
            [sys.executable, 'scripts/m017_probe.py', str(candidate), '--neural'], 'golden')):
        coverage = golden(GOLDEN, candidate, stage, deadline)
        atomic_json(output/'golden-coverage.json', coverage)
        stage('golden_coverage', lambda: require(not coverage['uncovered_arrays']
              and not coverage['uncovered_records'], 'Uncertified golden arrays or records'))
    stage('V1_canonical_outputs', lambda: v1_outputs(output, execute))
    stage('V1_archived_discrete', lambda: study_discrete(deadline))
    stage('M013', lambda: m013(output, execute))
    stage('M014', lambda: m014(output))
    stage('M015_reduced_scalar', lambda: m015(output, deadline))
    stage('M016_saved_recordings', lambda: m016(output, execute, sdk_python))

    # Preserve the historical raw study verdict. A mismatch here cannot be
    # promoted using only the separate canonical-output and RLS certificates.
    stage('V1_full_model_and_policy', lambda: execute(
        [sys.executable, str(V1/'verify_study.py'), str(V1/'m005b/primary'),
         str(output/'v1-full-model.json')], 'v1-full-model'))
    deadline.check()
    passed = captured is None and all(row['passed'] for row in results.values())
    atomic_json(output/'certificate.json', dict(stages=results, captured_input=captured is not None,
                stage_pass=passed, release_qualified=False, wall_s=time.monotonic()-started))
    return int(not passed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--captured-golden', type=Path)
    parser.add_argument('--sdk-python')
    args = parser.parse_args()
    sys.exit(run(args.output.resolve(), args.captured_golden, args.sdk_python))
