"""Fixed-input ridge and spectral diagnostics from preserved artifacts only."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.m027_residual_bounds import InformationCertificate, Enclosure, CertificateFailure
from tools.m027_spectral_bounds import singular_values, condition_interval


def run(output):
    from neuromancer.supervisor import Deadline, atomic_json
    output.mkdir(parents=True, exist_ok=False)
    deadline = Deadline.from_environment()
    rows = []
    failure = None
    try:
        reference_root = Path('reports/engineering/evidence/m017/golden_final')
        with np.load(reference_root/'outputs.npz') as archive:
            reference = dict(archive)
        records = json.loads((reference_root/'records.json').read_text())
        initial, z, target, _, _ = runpy.run_path('tests/test_predictive.py')['fixture']()
        if not np.array_equal(z, reference['initial_design']) or not np.array_equal(target, reference['initial_targets']):
            raise CertificateFailure('Fixed regression inputs differ; no silent input tolerance')
        design = Enclosure(z)
        penalty = Enclosure(np.diag(np.r_[0., np.ones(40)])).multiply(Enclosure(.1)).multiply(Enclosure(float(len(z))))
        information = design.transpose.product(design).add(penalty)
        rhs = design.transpose.product(Enclosure(target))
        certificate = InformationCertificate.from_equations(information, rhs)
        native = certificate.state(np.asarray(initial.record['coef']), initial.information_inverse)
        archived = certificate.state(reference['initial_theta'], reference['initial_information_inverse'])
        radius = np.nextafter(native['coefficient_radius']+archived['coefficient_radius'], np.inf)
        assert np.all(np.abs(np.asarray(initial.record['coef'])-reference['initial_theta']) <= radius)
        rows.append(dict(check='fixed_ridge', coefficient_comparison_radius=float(radius.max()),
                         inverse_contraction=native['contraction']))
        deadline.check()
        spectral = singular_values(z)
        archived_s = np.asarray(records['initial']['diagnostics']['singular_values'])
        if not np.all((archived_s >= spectral['lower']) & (archived_s <= spectral['upper'])):
            raise CertificateFailure('Archived singular values outside residual certificate')
        # Exact C02 structural nullspace, independently full-rank reduced columns.
        assert np.array_equal(z[:, 2::4], np.zeros_like(z[:, 2::4]))
        assert np.array_equal(z[:, 4::4], np.zeros_like(z[:, 4::4]))
        assert np.array_equal(z[:, 1::4], z[:, 3::4])
        reduced = np.c_[z[:, 0], z[:, 1::4]]
        reduced_s = singular_values(reduced)
        if reduced_s['lower'][-1] <= 0:
            raise CertificateFailure('Reduced C02 design rank not certified')
        assert records['initial']['diagnostics']['rank'] == 11
        rows.append(dict(check='C02_spectrum_and_structural_rank', certified_rank=11,
                         singular_value_radius=spectral['absolute_error'],
                         reduced_minimum_lower=float(reduced_s['lower'][-1])))
        source = Path('reports/research/evidence/m013/pilot_typed')
        summary = json.loads((source/'independent_analysis.json').read_text())
        for row in summary['rows']:
            deadline.check()
            with np.load(source/f"{row['network']}_{row['condition']}.npz") as archive:
                probe = np.column_stack((np.ones(len(archive['x_probe'])),
                    (archive['x_probe']-archive['mean'])/archive['scale']))
            lower, upper, result = condition_interval(probe)
            observed = float(np.linalg.cond(probe))
            if not lower <= row['probe_design_condition'] <= upper or not lower <= observed <= upper:
                raise CertificateFailure('M013 condition diagnostic outside spectral certificate')
            rows.append(dict(check='m013_probe_condition', network=row['network'], condition=row['condition'],
                             lower=lower, upper=upper, archived=row['probe_design_condition'],
                             observed=observed, singular_value_radius=result['absolute_error']))
    except (CertificateFailure, AssertionError, TimeoutError, np.linalg.LinAlgError) as error:
        failure = str(error) or type(error).__name__
    result = dict(fixed_problem_checks_pass=failure is None, checks=rows, failure=failure,
                  all_golden_families_certified=False, release_qualified=False)
    atomic_json(output/'certificate.json', result)
    print(json.dumps(result))
    return 0 if failure is None else 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    raise SystemExit(run(parser.parse_args().output))
