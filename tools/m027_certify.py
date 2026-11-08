"""Staged residual-based archive verification, never a release authorization."""
import argparse
import json
from pathlib import Path
import resource
import runpy
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.m027_residual_bounds import InformationCertificate, residual_planner_costs
from tools.portable_numeric_verification import CertificateFailure, certify_choice


def run(output, stage):
    from neuromancer.predictive import FIRModel
    from neuromancer.predictive_planner import plan
    from neuromancer.research_codec import model_digest
    from neuromancer.supervisor import Deadline, atomic_json
    output.mkdir(parents=True, exist_ok=False)
    deadline = Deadline.from_environment()
    started = time.monotonic_ns()
    cpu_started = time.process_time_ns()
    timings = {}
    checkpoints = []
    completed = 0
    digest_differences = 0
    location = {}
    failure = None
    max_theta_radius = 0.
    max_p_radius = 0.

    def elapsed(name, began):
        row = timings.setdefault(name, {'calls': 0, 'seconds': 0.})
        row['calls'] += 1
        row['seconds'] += (time.perf_counter_ns()-began)/1e9

    def progress():
        atomic_json(output/'progress.json', dict(stage=stage, completed_branches=completed,
                    checkpoints=checkpoints, location=location, timings=timings,
                    digest_differences=int(digest_differences), release_qualified=False))

    try:
        if stage == '256':
            fixture = runpy.run_path('tests/test_predictive.py')['fixture']()
            initial, _, _, inputs, rates = fixture
            model = FIRModel(initial.record, initial.information_inverse, 'RLS')
            certificate = InformationCertificate(model.theta, model.p)
            for index in range(256):
                deadline.check()
                k = 2400+index%100
                x = np.concatenate([inputs[k-lag] for lag in range(10)])
                certificate.update(model.standardized(x), rates[k]-model.record['output_mean'])
                model.update(x, rates[k])
                if model.failure:
                    raise CertificateFailure(model.failure)
                state = certificate.state(model.theta, model.p)
                max_theta_radius = max(max_theta_radius, float(state['coefficient_radius'].max()))
                max_p_radius = max(max_p_radius, state['covariance_radius'])
            completed = 1
        else:
            root = Path('reports/evidence/v1_finish/m005b/primary')
            jobs = json.loads((root/'provenance.json').read_text())['jobs']
            if stage == 'first':
                jobs = jobs[:1]
            elif stage == 'dependency':
                jobs = [job for job in jobs if list(job)==[5, 47]]
            for network, replicate in jobs:
                directory = root/f'n{network}_r{replicate}'
                initial = json.loads((directory/'initial.json').read_text())
                with np.load(directory/'initial.npz') as archive:
                    starting = dict(archive)
                branches = [branch for branch in json.loads((directory/'trial.json').read_text())['branches']
                            if branch['controller']=='RLS-MPC']
                if stage == 'first':
                    branches = branches[:1]
                elif stage == 'dependency':
                    branches = [branch for branch in branches if branch['name']=='LOSS_RLS-MPC']
                for branch in branches:
                    name = branch['name']
                    began = time.perf_counter_ns()
                    with np.load(directory/(name+'.npz')) as archive:
                        data = dict(archive)
                    inputs = data['delivered']
                    history = np.vstack([starting['history'], inputs])
                    raw = data['counts'].reshape(len(inputs), 4, 5)[:, :, :4].sum(axis=2)/.4
                    elapsed('archive_load', began)
                    model = FIRModel(initial['record'], starting['p'], 'RLS')
                    certificate = InformationCertificate(model.theta, model.p)
                    branch_started = time.monotonic_ns()
                    for step in range(len(inputs)):
                        location = dict(network=network, replicate=replicate, branch=name, step=step)
                        deadline.check()
                        if step%50 == 0:
                            began = time.perf_counter_ns()
                            with np.load(directory/f'{name}_plan_{step//50:02}.npz') as archive:
                                saved = dict(archive)
                            elapsed('plan_load', began)
                            past = history[step:step+9]
                            if not np.array_equal(past, saved['history']):
                                raise CertificateFailure('Archived planner history differs')
                            began = time.perf_counter_ns()
                            native = plan(model.record, model.theta, past, initial['calibration']['target_hz'],
                                          int(saved['origin_us']), clock=lambda: 0)
                            elapsed('native_planner', began)
                            archived_p = starting['p'] if step==0 else data['dense_p'][step//50-1]
                            began = time.perf_counter_ns()
                            costs, left, right = residual_planner_costs(certificate, model.record,
                                model.theta, model.p, saved['theta'], archived_p, past,
                                initial['calibration']['target_hz'], native)
                            elapsed('planner_certificate', began)
                            if not costs.contains(saved['cost']):
                                raise CertificateFailure('Archived costs outside residual certificate')
                            chosen = int(saved['chosen'])
                            if native['chosen'] != chosen:
                                raise CertificateFailure('Native planner decision differs')
                            certify_choice(costs, chosen,
                                           np.repeat(np.arange(0., 121., 5.), 25),
                                           np.tile(np.arange(0., 121., 5.), 25), native['bank'])
                            if not np.array_equal(inputs[step:step+50], native['first']):
                                raise CertificateFailure('Delivered four-channel policy differs')
                            checkpoints.append(dict(**location, theta_radius=float(left['coefficient_radius'].max()),
                                covariance_radius=left['covariance_radius'], cost_radius=float(costs.radius.max()),
                                contraction=left['contraction']))
                            began = time.perf_counter_ns()
                            progress()
                            elapsed('progress_write', began)
                        x = history[step:step+10][::-1].ravel()
                        z = model.standardized(x)
                        eligible = int(data['frames'][step, 5]) > model.updates
                        if eligible:
                            began = time.perf_counter_ns()
                            certificate.update(z, raw[step]-model.record['output_mean'])
                            elapsed('information_update', began)
                        began = time.perf_counter_ns()
                        model.update(x, raw[step], eligible)
                        elapsed('native_update', began)
                        if model.failure:
                            raise CertificateFailure('Native RLS failure: '+model.failure)
                        began = time.perf_counter_ns()
                        state = certificate.state(model.theta, model.p)
                        elapsed('state_residual', began)
                        max_theta_radius = max(max_theta_radius, float(state['coefficient_radius'].max()))
                        max_p_radius = max(max_p_radius, state['covariance_radius'])
                        began = time.perf_counter_ns()
                        digest_differences += model_digest(model) != data['state_hashes'][step].tobytes()
                        elapsed('digest', began)
                        if (step+1)%50 == 0:
                            archived_state = certificate.state(data['dense_theta'][step//50], data['dense_p'][step//50])
                            # A posteriori comparison through the same ideal equation, no reset.
                            theta_limit = state['coefficient_radius']+archived_state['coefficient_radius']
                            if np.any(np.abs(model.theta-data['dense_theta'][step//50]) > np.nextafter(theta_limit, np.inf)):
                                raise CertificateFailure('Dense coefficients exceed residual comparison')
                            covariance_limit = np.nextafter(state['covariance_radius']+archived_state['covariance_radius'], np.inf)
                            if np.any(np.abs(model.p-data['dense_p'][step//50]) > covariance_limit):
                                raise CertificateFailure('Dense covariance exceeds residual comparison')
                    completed += 1
                    checkpoints.append(dict(network=network, replicate=replicate, branch=name,
                        completed=True, branch_wall_s=(time.monotonic_ns()-branch_started)/1e9))
                    progress()
    except (CertificateFailure, TimeoutError, ValueError, np.linalg.LinAlgError) as error:
        failure = dict(**location, reason=str(error))
    result = dict(stage=stage, method='continuous-information-residual-v1', completed_branches=completed,
        prescribed_branches=40 if stage=='all' else 1, failure=failure,
        stage_pass=failure is None and completed==(40 if stage=='all' else 1),
        maximum_coefficient_radius=max_theta_radius, maximum_covariance_radius=max_p_radius,
        wall_s=(time.monotonic_ns()-started)/1e9, cpu_s=(time.process_time_ns()-cpu_started)/1e9,
        peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, checkpoints=checkpoints,
        timings=timings, digest_differences=int(digest_differences), release_qualified=False)
    atomic_json(output/'certificate.json', result)
    print(json.dumps({key:value for key,value in result.items() if key!='checkpoints'}))
    return 0 if result['stage_pass'] else 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--stage', choices=['256', 'first', 'dependency', 'all'], required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.output, args.stage))
