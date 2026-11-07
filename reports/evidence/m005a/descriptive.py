"""TUNE-only descriptive exports after resource stop; NEVER selects a PI."""
import argparse,json,time
from pathlib import Path
import numpy as np
from analyze import trial_rows,csvout,ci


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True)
    began=time.perf_counter();rows=[];traces=[];designs=[];meta=json.loads((a.raw/'provenance.json').read_text())
    for folder in sorted(a.raw.glob('n*_r*')):
        r,t,d=trial_rows(folder);rows+=r;traces+=t;designs+=d
    csvout(a.output/'metrics.csv',rows);csvout(a.output/'traces.csv',traces)
    (a.output/'excitation.json').write_text(json.dumps(designs,indent=2)+'\n')
    networks=[];summary={}
    for name in meta['names']:
        summary[name]={}
        for condition,window in [('STATIC','stationary'),('LOSS','late')]:
            selected=[r for r in rows if (r['controller'],r['condition'],r['window'])==(name,condition,window)]
            summary[name][condition]={'mean_mae_hz':float(np.mean([r['mae_hz'] for r in selected])),
                                      'mean_bias_hz':float(np.mean([r['bias_hz'] for r in selected])),
                                      'mean_nominal_charge_pC':float(np.mean([r['total_charge_pC'] for r in selected]))}
            networks+=selected
    csvout(a.output/'network_models.csv',networks)
    gates=[]
    for n in range(10):
        folder=a.raw/f'n{n}_r40';m=json.loads((folder/'trial.json').read_text());c=m['calibration']
        for condition in ('STATIC','LOSS'):
            def mean(name,key):return next(r[key] for r in rows if (r['network'],r['controller'],r['condition'],r['window'])==(n,name,condition,'late'))
            gates.append(dict(network=n,condition=condition,calibration_valid=c['valid'],baseline_hz=c['baseline_hz'],noise_hz=c['noise_hz'],target_hz=c['target_hz'],qff_pA=c['feedforward_pA'],authority_hz=mean('MAX','rate_hz')-mean('ZERO','rate_hz')))
    csvout(a.output/'authority_calibration.csv',gates)
    record=dict(status='DESCRIPTIVE_TUNING_ONLY',execution='PARTIAL_RESOURCE_CAP',scientific='NOT_QUALIFIED',m005b='HOLD',
                selected_controller=None,confirmation_trials=0,networks=10,replicates=[40],branches=120,models=summary,
                invalid_calibrations=sum(not json.loads((f/'calibration.json').read_text())['valid'] for f in a.raw.glob('n*_r*')),
                fallback_decisions=sum(r['fallback_decisions'] for r in rows if r['window']=='full'),wall_s=time.perf_counter()-began)
    (a.output/'descriptive_summary.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n');print(json.dumps(record,indent=2))


if __name__=='__main__':main()
