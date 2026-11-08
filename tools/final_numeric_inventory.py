"""Inventory immutable closure arrays and decision records, without rescoring trials."""
import argparse
import csv
import io
import json
from pathlib import Path
import tarfile

import numpy as np
from final_numeric_diagnosis import difference


def operation(name):
    if name.startswith('planner_'):
        if name.endswith(('first', 'bank')):
            return 'actuator_action', 'finite candidate bank and slew projection', 'Exact discrete-policy requirement'
        if name.endswith(('dose', 'switch', 'exposure')):
            return 'floating_objective', 'sums of fixed delivered currents', 'Fixed candidate currents, no fitted model'
        return 'floating_prediction', 'coefficient scaling, lagged products, horizon means and squared tracking error', 'Regularized fit error propagates through 10 lags and squared objective'
    if name.endswith('actions') or name in ('cue_schedule', 'pi_state', 'feedback_pi_state'):
        return 'controller_state_or_action', 'PI arithmetic or planner selection followed by actuator projection', 'Exact state/action requirement'
    if name in ('spike_i', 'spike_us', 'neural_counts', 'neural_sector', 'reservoir_final', 'reservoir_history'):
        return 'neural_event_or_observation', 'fixed random streams, neural integration and causal spike aggregation', 'Threshold discontinuities require exact event and observation checks'
    if name == 'dag_edges':
        return 'mixed_graph', 'pre/post indices, ampere-to-pA weight conversion and integer delays', 'Graph columns 0, 1, 3 exact, floating weight column assessed separately'
    if name.startswith('initial_'):
        return 'floating_fit', 'standardization, Z.T@Z, Z.T@Y, LAPACK solve and inverse', 'Unregularized design rank 11/41, regularized Gram condition about 58.05'
    if name in ('eligibility', 'reward_weights'):
        return 'plasticity_state', 'trace decay, reward product, summation and clipping', 'Exact historical mechanism outputs remain required'
    if name.startswith('decoder_'):
        return 'floating_readout', 'standardized ridge solve and linear readout multiplication', 'Probe-training design and regularization fixed'
    if name.endswith('_prediction'):
        return 'floating_forecast', 'augmented least-squares fit and recursive AR/ARX matrix-vector products', 'Report model penalized condition separately, recursive errors may propagate'
    return 'floating_adaptive_state', 'FIR dot products, rank-one RLS covariance/coefficient updates or windowed refits', 'RLS feedback through covariance, gain and residual requires trajectory bounds'


def read_archive(root, filename, prefix):
    with tarfile.open(root/filename) as tar:
        arrays = np.load(io.BytesIO(tar.extractfile(prefix+'/outputs.npz').read()))
        records = json.loads(tar.extractfile(prefix+'/records.json').read())
        return dict(arrays), records


def json_differences(a, b, path=''):
    rows = []
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for key in a:
            rows.extend(json_differences(a[key], b[key], path+'/'+key))
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for index, (left, right) in enumerate(zip(a, b, strict=True)):
            rows.extend(json_differences(left, right, path+'/'+str(index)))
    elif a != b:
        rows.append(dict(path=path, reference=a, observed=b))
    return rows


def inventory(output):
    output.mkdir(parents=True, exist_ok=False)
    source = Path('reports/engineering/evidence/final_core_closure')
    base = Path('reports/engineering/evidence/m017/golden_final')
    reference = dict(np.load(base/'outputs.npz'))
    original_records = json.loads((base/'records.json').read_text())
    platforms = dict(
        local=read_archive(source, 'local-qualification.tar.gz', 'local/golden'),
        linux=read_archive(source, 'hosted-closure.tar.gz', 'hosted/closure-linux/golden'),
        macos_intel=read_archive(source, 'hosted-closure.tar.gz', 'hosted/closure-macos/golden'))
    rows = []
    decisions = {}
    for platform, (arrays, records) in platforms.items():
        assert arrays.keys() == reference.keys()
        for name, expected in reference.items():
            category, calculation, conditioning = operation(name)
            row = dict(platform=platform, name=name, category=category,
                       likely_operation=calculation, conditioning=conditioning,
                       **difference(expected, arrays[name]))
            if expected.ndim == 2 and expected.shape == (41, 41):
                row['observed_condition_number'] = float(np.linalg.cond(arrays[name]))
            if name == 'dag_edges':
                row['discrete_graph_columns_exact'] = all(
                    difference(expected[:, index], arrays[name][:, index])['exact'] for index in (0, 1, 3))
            rows.append(row)
        changed = json_differences(original_records, records)
        decisions[platform] = dict(records_differences=changed,
            qualification_exact=original_records['qualification'] == records['qualification'],
            bootstrap_exact=original_records['bootstrap'] == records['bootstrap'],
            choices_exact=all(original_records[key] == records[key] for key in original_records if key.endswith('_chosen')),
            controller_events_exact=all(original_records[key] == records[key] for key in ('FIXED_events', 'RLS_events')),
            native_replay_record_exact=original_records['neural_replay'] == records['neural_replay'])
        for name in ('AR1', 'AR4', 'ARX1', 'ARX4', 'SHUFFLED1', 'SHUFFLED4'):
            decisions[platform][name+'_conditioning'] = records[name]['diagnostics']
    summaries = {}
    for platform in platforms:
        selected = [row for row in rows if row['platform'] == platform]
        summaries[platform] = dict(arrays=len(selected), exact=sum(row['exact'] for row in selected),
                                   maximum_absolute_error=max(row['max_absolute_error'] for row in selected),
                                   maximum_relative_error_nonzero=max(row['max_relative_error_nonzero'] for row in selected),
                                   maximum_ulp_distance=max(row.get('max_ulp_distance', 0) for row in selected))
    (output/'array-inventory.json').write_text(json.dumps(dict(summary=summaries, arrays=rows), indent=2, allow_nan=False)+'\n')
    fields = sorted({key for row in rows for key in row})
    with (output/'array-inventory.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (output/'decision-inventory.json').write_text(json.dumps(decisions, indent=2, allow_nan=False)+'\n')
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    inventory(parser.parse_args().output)
