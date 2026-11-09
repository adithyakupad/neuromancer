"""Portable, fail-closed reconstruction of the original V1 study audit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from neuromancer.predictive import FIRModel
from neuromancer.predictive_planner import bank
from neuromancer.research_codec import model_digest
from neuromancer.supervisor import Deadline, atomic_json
from tools import m029_parallel
from tools.m027_residual_bounds import check_fixed_objective, expression_magnitude, planner_queries
from tools.m029_fits import Ball, exact, maximum, members, require
from tools.m029_remaining import run as remaining
from tools.m030_v1 import ROOT, archived_npz, first_digest, model_portability, raw_inputs, read
from tools.portable_numeric_verification import certify_choice, gamma, positive_add, positive_multiply

M029_EVIDENCE = Path('reports/engineering/evidence/m029_final_release')
M029_SOURCE = 'ee2c519d62188dc234d0cce9fb31dd2efe911277'


def extract_m029(output, variant):
    name = 'numerical-attempts.tar.gz'
    manifest = read(M029_EVIDENCE/'artifact-manifest.json')
    archive = M029_EVIDENCE/name
    require(m029_parallel.sha(archive) == manifest['files'][name]['sha256'], 'M029 archive hash differs')
    prefix = 'm029/local-ordered/' if variant == 'reference' else 'm029/ordered-hosted-linux/matrix/'
    with tarfile.open(archive) as tar:
        files = [entry for entry in tar if entry.name.startswith(prefix)
                 and (entry.name[len(prefix):].startswith('full/') or entry.name == prefix+'qualification.json')]
        require(files, 'M029 evidence matrix absent')
        tar.extractall(output, members=files, filter='data')
    return output/prefix


def qualified_rls(matrix, *, archive_exact):
    qualification = read(matrix/'qualification.json')
    stage = read(matrix/'full/stage.json')
    supervisor = read(matrix/'full/supervisor-result.json')
    schedule = read(matrix/'full/schedule.json')
    launcher = read(matrix/'full/launcher.json')
    expected = m029_parallel.manifest()
    require(qualification['passed'] and qualification['branches'] == 40
            and stage['stage_pass'] and stage['requested_branches'] == 40
            and stage['source'] == qualification['source'] == schedule['source'] == M029_SOURCE
            and schedule['branches'] == expected and supervisor['status'] == 'COMPLETED'
            and supervisor['cleanup_verified'] and not launcher['watchdog_intervened']
            and not launcher['surviving_groups'] and supervisor['deadline_ns'] == schedule['deadline_ns']
            and supervisor['finished_ns'] < supervisor['deadline_ns'], 'M029 RLS matrix is unqualified')
    rows = {}
    for i, (identity, worker) in enumerate(zip(expected, supervisor['workers'], strict=True)):
        folder = matrix/'full'/f'branch-{i:02}'
        row = m029_parallel.verify_worker(folder, identity, M029_SOURCE, worker, supervisor, schedule['kernel_sha256'])
        require(row == stage['rows'][i], 'M029 aggregate and checked branch differ')
        certificate = read(folder/'certificate.json')
        if archive_exact:
            require(certificate['digest_differences'] == 0, 'Reference RLS states do not authenticate every archived digest')
        rows[tuple(identity)] = dict(row=row, certificate=certificate)
    return rows


def rls_forecasts(output, deadline, candidate, reference):
    rows = []
    for identity, item in candidate.items():
        deadline.check()
        network, replicate, branch = identity
        folder = ROOT/f'n{network}_r{replicate}'
        initial = archived_npz(folder/'initial.npz')
        record = read(folder/'initial.json')['record']
        data, x, y = raw_inputs(folder, branch, initial)
        model = FIRModel(record, initial['p'], 'RLS')
        trajectory = hashlib.sha256()
        theta, native, z = [], [], []
        for i, (features, observed) in enumerate(zip(x, y, strict=True)):
            deadline.check()
            z.append(model.standardized(features))
            theta.append(model.theta)
            native.append(model.predict(features))
            require(data['frames'][i, 5] == i+1, 'RLS eligibility differs')
            model.update(features, observed)
            require(model.failure is None and model.updates == i+1, 'Native RLS update failed')
            trajectory.update(model_digest(model))
        require(trajectory.hexdigest() == item['row']['native_state_trajectory_sha256'],
                f'Fresh RLS state trajectory differs from qualified certificate for {identity}')
        radius = positive_add(item['certificate']['maximum_coefficient_radius'],
                              reference[identity]['certificate']['maximum_coefficient_radius']).item()
        # The two continuous certificates share the exact initial state and
        # original inputs. Their coefficient error bounds add by triangle inequality.
        prediction = Ball(np.asarray(z)[:, :, None]).multiply(Ball(np.asarray(theta), radius))
        prediction = prediction.mean((1,)).multiply(Ball(41.)).add(Ball(record['output_mean']))
        require(maximum(prediction) <= 100., 'RLS archived forecast guard crossed')
        members(prediction, 'Every native and archived RLS pre-update prediction',
                np.asarray(native), data['pre_prediction'])
        rows.append(dict(branch=list(identity), forecasts=len(theta), states=len(theta),
                         trajectory_sha256=trajectory.hexdigest(), prediction_radius=float(prediction.radius.max())))
        atomic_json(output/'rls-progress.json', dict(branches=rows, release_qualified=False))
    return rows


def projected(request, previous):
    lower, upper = np.maximum(0., previous-30), np.minimum(120., previous+30)
    for _ in range(64):
        low = previous-lower > 30
        high = upper-previous > 30
        if not (low.any() or high.any()):
            return np.clip(request, lower, upper)
        lower[low] = np.nextafter(lower[low], previous[low])
        upper[high] = np.nextafter(upper[high], previous[high])
    raise ValueError('Cannot represent exact actuator bounds')


def scalar_policy(branch, calibration, data, previous):
    kind = branch['controller']
    require(data['presented'].all() and (calibration['valid'] or kind in ('MAX', 'ZERO')),
            'Unexpected scalar policy fallback')
    ff, target = calibration['feedforward_pA'], calibration['target_hz']
    q = 0. if kind == 'ZERO' else 120. if kind == 'MAX' else ff
    prior = np.array([q, 0., np.nan, 0., 0., 0., 0.])
    integral = 0.
    rows, commands = [], []
    rates = data['counts'].reshape(-1, 4, 5)[:, :, :4].sum(axis=(1, 2)).reshape(64, 50)
    for second, block in enumerate(rates, start=1):
        commands.extend([q]*50)
        rows.extend([prior]*49)
        error = target-sum(float(count)/1.6 for count in block)/50
        blocked = clipped = False
        if kind == 'PI10_5':
            proposed = min(120., max(-120., integral+5*error))
            raw = ff+10*error+proposed
            blocked = (raw > 120 and error > 0) or (raw < 0 and error < 0)
            if not blocked:
                integral = proposed
            raw = ff+10*error+integral
            q = min(120., max(0., raw))
            clipped = raw != q
        prior = np.array([q, integral, error, float(blocked), float(clipped), 0., second])
        rows.append(prior)
    times = np.arange(51_020_000, 115_000_001, 20_000)
    exact(np.c_[times, rows], data['frames'], 'Scalar policy frames')
    first = projected(np.asarray(commands), np.r_[previous, data['delivered'][:-1, 0]])
    exact(np.c_[first, np.zeros(3200), first, np.zeros(3200)], data['delivered'], 'Scalar policy delivered actions')


def compact_plans(output, deadline, bias_bounds, bias_names):
    from neuromancer.predictive_planner import GRID

    q0, q1 = np.repeat(GRID, len(GRID)), np.tile(GRID, len(GRID))
    bias_index = {name: i for i, name in enumerate(bias_names)}
    rows = []
    for n, rep in read(ROOT/'provenance.json')['jobs']:
        folder = ROOT/f'n{n}_r{rep}'
        initial = archived_npz(folder/'initial.npz')
        meta = read(folder/'initial.json')
        record, calibration = meta['record'], meta['calibration']
        theta0 = np.asarray(record['coef'])
        cache = {}
        noise = None
        for branch in read(folder/'trial.json')['branches']:
            deadline.check()
            require(branch['fault'] is None and branch['safe_bins'] == branch['violations'] == 0
                    and branch['model_failure'] is None, 'Original archived branch has a failure')
            if noise is None:
                noise = branch['noise']
            require(branch['noise'] == noise, 'Trial input noise provenance differs')
            name = branch['name']
            data = archived_npz(folder/(name+'.npz'))
            exposure = Ball(data['delivered']).mean((0, 1)).multiply(Ball(data['delivered'].size*.02))
            members(exposure, 'Archived stimulation exposure', branch['exposure_pA_s'],
                    data['delivered'].sum()*.02)
            if not branch['controller'].endswith('-MPC'):
                scalar_policy(branch, calibration, data, initial['history'][-1, 0])
                rows.append(dict(branch=[n, rep, name], exact_actions=3200, candidate_scores=0))
                continue
            history = np.vstack([initial['history'], data['delivered']])
            commands = []
            for index in range(64):
                deadline.check()
                step = 50*index
                saved = archived_npz(folder/f'{name}_plan_{index:02}.npz')
                exact(int(saved['origin_us']), 51_000_000+20_000*step, 'Planner forecast origin')
                exact(saved['history'], history[step:step+9], 'Exact original candidate history')
                theta = saved['theta']
                exact(theta, theta0 if not index else data['dense_theta'][index-1], 'Stored planner model')
                h = saved['history']
                key = h.tobytes()
                if key not in cache:
                    _, _, actions = bank(h[-1, 0])
                    dose = .02*np.sum(.02*(actions/120)**2, axis=1)
                    switch = .01*((q0-h[-1, 0])**2+(q1-q0)**2)/120**2
                    fixed = dict(dose=dose, switch=switch, exposure=actions.sum(1)*.02*2)
                    cache[key] = actions, fixed, planner_queries(record, h, actions)
                actions, fixed, queries = cache[key]
                check_fixed_objective(fixed, saved)
                absolute = expression_magnitude(record, theta)
                intercept_radius = 0.
                identity = n, rep, name
                if identity in bias_index:
                    current = bias_bounds.part((step, bias_index[identity]))
                    intercept_radius = maximum(current.subtract(Ball(theta[0])))
                rounding = positive_multiply(2*gamma(512), positive_add(absolute, intercept_radius))
                extra = positive_add(rounding, intercept_radius)
                require(positive_add(absolute, intercept_radius) <= 100., 'Archive planner guard crossed')
                means = queries.product(Ball(theta)).add(Ball(record['output_mean'])).mean((1,)).reshape((625, 2))
                means = Ball(means.center, positive_add(means.radius, extra))
                error = means.subtract(Ball(calibration['target_hz']))
                tracking = error.multiply(error).mean((1,)).multiply(Ball(2.))
                cost = tracking.add(Ball(fixed['dose'])).add(Ball(fixed['switch']))
                members(tracking, 'Archived candidate tracking', saved['tracking'])
                members(cost, 'Archived candidate objective', saved['cost'])
                chosen = int(saved['chosen'])
                certify_choice(cost, chosen, q0, q1, actions)
                exact(float(saved['q0']), float(q0[chosen]), 'Chosen first setpoint')
                exact(float(saved['q1']), float(q1[chosen]), 'Chosen second setpoint')
                expected = np.c_[actions[chosen, :50], np.zeros(50), actions[chosen, :50], np.zeros(50)]
                exact(expected, data['delivered'][step:step+50], 'Original delivered candidate policy')
                commands.extend([q0[chosen]]*50)
                future = np.vstack([h, np.c_[actions[chosen], np.zeros(100), actions[chosen], np.zeros(100)]])
                lagged = np.lib.stride_tricks.sliding_window_view(future, 10, axis=0)
                x = lagged[:, :, ::-1].transpose(0, 2, 1).reshape(100, 40)
                x = Ball(x).subtract(Ball(record['mean'])).divide_positive(Ball(record['scale']))
                z = Ball(np.c_[np.ones(100), x.center], np.c_[np.zeros(100), x.radius])
                forecast = z.product(Ball(theta)).add(Ball(record['output_mean']))
                members(Ball(forecast.center, positive_add(forecast.radius, extra)),
                        'Archived selected forecast', saved['selected_forecast'])
            require(branch['plans'] == 64 and data['presented'].all(), 'Incomplete original planner decisions')
            frames = data['frames']
            bins = np.arange(1, 3201)
            updates = np.zeros(3200) if branch['controller'] == 'FIXED-MPC' else bins
            exact(np.c_[51_000_000+20_000*bins, commands, np.zeros(3200), np.full(3200, 4),
                        bins, updates, np.zeros(3200), np.zeros(3200)], frames, 'Exact original MPC state transitions')
            rows.append(dict(branch=[n, rep, name], exact_actions=3200, candidate_scores=40000))
        atomic_json(output/'policy-progress.json', dict(branches=rows, release_qualified=False))
    return rows


def run(output, sdk, rls_variant):
    deadline = Deadline.from_environment()
    output.mkdir(parents=True, exist_ok=False)
    remaining(output/'original-checks', None, sdk)
    old = read(output/'original-checks/certificate.json')
    require(all(row['passed'] for name, row in old['stages'].items() if name != 'V1_full_model_and_policy'),
            'Other preserved numerical families did not pass')
    first_digest(output/'first-digest')
    models, bias, branches = model_portability(output/'models', deadline)
    policy = compact_plans(output, deadline, bias, branches)
    rls = []
    if rls_variant:
        references = qualified_rls(extract_m029(output/'matrix-reference', 'reference'), archive_exact=True)
        candidates = references if rls_variant == 'reference' else qualified_rls(
            extract_m029(output/'matrix-native', 'linux'), archive_exact=False)
        rls = rls_forecasts(output, deadline, candidates, references)
    deadline.check()
    passed = len(rls) == 40 and len(policy) == 260
    atomic_json(output/'certificate.json', dict(first_digest=True, model_states=models['model_states'],
        exact_policy_actions=sum(row['exact_actions'] for row in policy),
        candidate_scores=sum(row['candidate_scores'] for row in policy),
        rls=rls, full_V1_portability=passed, release_qualified=False,
        blocker=None if passed else 'A complete qualified native Intel RLS matrix is required'))
    deadline.check()
    return int(not passed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=lambda path: Path(path).resolve())
    parser.add_argument('--sdk-python', required=True)
    parser.add_argument('--rls', choices=['reference', 'linux'])
    args = parser.parse_args()
    sys.exit(run(args.output, args.sdk_python, args.rls))
