"""Descriptive report aggregation of preregistered endpoints; no model selection."""
import csv
import json
from pathlib import Path
import numpy as np

base = Path('reports/evidence/m003_2/results'); analysis = base/'analysis'
d = np.load(analysis/'data.npz'); selected = json.loads((base/'models/selected.json').read_text())
trials = [json.loads(p.read_text()) for p in sorted((base/'raw').glob('n*/trial.json'))]
summary = json.loads((base/'raw/summary.json').read_text()); rows = list(csv.DictReader((analysis/'episodes.csv').open()))
origins = list(csv.DictReader((analysis/'origins.csv').open())); null = list(csv.DictReader((analysis/'null.csv').open()))
families = ('FIR', 'STATE', 'STATE_SHUFFLED', 'FIR_SHUFFLED', 'ARX')
report = dict(trials=len(trials), origins=sum(len(t['origins']) for t in trials), restored_branches=sum(len(t['branch_costs']) for t in trials),
              simulated_s=3339, acquisition_wall_s=summary['wall_ns']/1e9,
              aggregate_simulated_s_per_wall_s=3339/(summary['wall_ns']/1e9),
              peak_worker_rss_bytes=max(t['peak_rss_bytes'] for t in trials),
              initialization_s_range=[min(t['engine']['initialization_ns'] for t in trials)/1e9, max(t['engine']['initialization_ns'] for t in trials)/1e9],
              constraint_violations=sum(b['violations'] for t in trials for b in t['branch_costs']))
report['models'] = {}
for family in families:
    rr = [r for r in rows if r['model'] == family and r['horizon_ms'] == '1000' and r['action'] != 'S']
    models = [m for k, m in selected.items() if k.endswith('_'+family)]
    report['models'][family] = dict(primary_bias_hz=float(np.mean([float(r['bias_hz']) for r in rr])),
        coverage=float(np.mean([float(r['coverage']) for r in rr])), interval_halfwidth_hz=float(np.mean([float(r['interval_halfwidth_hz']) for r in rr])),
        rank_range=[min(m['diagnostics']['rank'] for m in models), max(m['diagnostics']['rank'] for m in models)],
        condition_range=[min(m['diagnostics']['condition'] for m in models), max(m['diagnostics']['condition'] for m in models)],
        augmented_condition_max=max(m['diagnostics']['augmented_condition'] for m in models), parameters=models[0]['diagnostics']['parameters'],
        null_one_second_false_response_rms_hz_range=[min(float(r['one_second_false_response_rms_hz']) for r in null if r['model']==family),max(float(r['one_second_false_response_rms_hz']) for r in null if r['model']==family)])
report['reserved_origins'] = {}
for s in ('LOW', 'HIGH'):
    rr = [r for r in origins if r['stratum']==s and int(r['replicate']) in (29,30)]
    report['reserved_origins'][s] = dict(rate_hz_range=[min(float(r['rate_hz']) for r in rr),max(float(r['rate_hz']) for r in rr)],
        time_s_range=[min(float(r['origin_s']) for r in rr),max(float(r['origin_s']) for r in rr)])
x = d['interaction'][:,2].mean(axis=1); draws = np.random.default_rng(20261102).integers(0,10,(10000,10))
report['pooled_high_minus_low_hz'] = float(x.mean()); report['pooled_high_minus_low_ci'] = np.quantile(x[draws].mean(axis=1),[.025,.975]).tolist()
report['descriptive_only'] = 'Aggregation of frozen endpoints; no new gate or model selection'
(analysis/'report_summary.json').write_text(json.dumps(report,indent=2)+'\n')
with (analysis/'network_replicate.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['network','replicate','model','one_second_mse_hz2'])
    for n in range(10):
        for r, rep in enumerate((29,30)):
            for m, family in enumerate(families):w.writerow([n,rep,family,float(d['errors'][n,r,m,:,1:,2].mean())])
with (analysis/'network_interaction.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['network','one_second_high_minus_low_mean_sector_hz'])
    for n in range(10):w.writerow([n,float(x[n])])
print(json.dumps(report,indent=2))
