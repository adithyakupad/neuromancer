"""Offline audit of immutable objective terms and planner magnitude guards."""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.m027_residual_bounds import check_fixed_objective, expression_magnitude, CertificateFailure


def run(output):
    from neuromancer.predictive_planner import bank
    from neuromancer.supervisor import Deadline, atomic_json
    output.mkdir(parents=True, exist_ok=False)
    deadline = Deadline.from_environment()
    root = Path('reports/evidence/v1_finish/m005b/primary')
    cache = {}
    count = 0
    maximum = 0.
    started = time.monotonic_ns()
    failure = None
    try:
        for network, replicate in json.loads((root/'provenance.json').read_text())['jobs']:
            directory = root/f'n{network}_r{replicate}'
            record = json.loads((directory/'initial.json').read_text())['record']
            for branch in json.loads((directory/'trial.json').read_text())['branches']:
                if branch['controller'] != 'RLS-MPC':
                    continue
                for index in range(64):
                    deadline.check()
                    with np.load(directory/f"{branch['name']}_plan_{index:02}.npz") as archive:
                        saved = dict(archive)
                    previous = float(saved['history'][-1, 0])
                    key = previous.hex()
                    if key not in cache:
                        q0, q1, q = bank(previous)
                        cache[key] = dict(
                            dose=.02*np.sum(.02*(q/120)**2, axis=1),
                            switch=.01*((q0-previous)**2+(q1-q0)**2)/120**2,
                            exposure=q.sum(1)*.02*2,
                        )
                    check_fixed_objective(cache[key], saved)
                    maximum = max(maximum, expression_magnitude(record, saved['theta']))
                    count += 1
    except (CertificateFailure, TimeoutError) as error:
        failure = dict(network=network, replicate=replicate, branch=branch['name'], plan=index, reason=str(error))
    result = dict(plans=count, prescribed_plans=2560, fixed_terms_pass=count==2560 and failure is None,
                  failure=failure, maximum_expression_hz=maximum, immutable_bank_states=len(cache),
                  wall_s=(time.monotonic_ns()-started)/1e9, release_qualified=False)
    atomic_json(output/'certificate.json', result)
    print(json.dumps(result))
    return 0 if result['fixed_terms_pass'] else 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    raise SystemExit(run(parser.parse_args().output))
