"""One-lag count FIR/RLS shadow replay after SDK PI qualification."""
import json
from pathlib import Path
import sys
import numpy as np


def read(path):
    return json.loads(path.read_text())


def main(root):
    qualified=read(root.with_name(root.name+'_verification.json'))
    assert qualified['all_paired_receipts'] and qualified['cases']['PI']['commits']>0
    calibration=read(root/'C1'/'ticks.json')[:8]
    design=np.array([[1.,float(bool(row['receipts']))] for row in calibration])
    targets=np.array([row['counts'][0] for row in calibration])
    information=design.T@design+np.diag([0.,.1])
    covariance=np.linalg.inv(information)
    frozen=np.linalg.solve(information,design.T@targets)
    adaptive=frozen.copy()
    trace=[]
    previous=None
    for row in read(root/'PI'/'ticks.json'):
        # Predict using the previously accepted proposal before consuming this bin.
        planned=bool(previous and previous['decision'] and previous['decision']['accepted'])
        features=np.array([1.,float(planned)])
        fixed_value=float(features@frozen)
        adaptive_value=float(features@adaptive)
        observed=row['counts'][0]
        confirmed=bool(row['receipts'])
        update=row['valid'] and planned==confirmed
        if update:
            gain=covariance@features/(.999+features@covariance@features)
            adaptive+=gain*(observed-adaptive_value)
            covariance=(covariance-np.outer(gain,features@covariance))/.999
            covariance=(covariance+covariance.T)/2
            assert np.isfinite(adaptive).all() and np.linalg.eigvalsh(covariance).min()>0
        trace.append(dict(stop_frame=row['stop'],planned=planned,confirmed=confirmed,
            observed_count=observed,frozen_prediction=fixed_value,rls_prediction=adaptive_value,
            updated=update,rls_coefficients=adaptive.tolist()))
        previous=row
    result=dict(mode='offline_sdk_receipt_shadow',fit_bins=8,test_bins=len(trace),
        update_bins=sum(row['updated'] for row in trace),frozen_coefficients=frozen.tolist(),
        frozen_mae=float(np.mean([abs(row['observed_count']-row['frozen_prediction']) for row in trace])),
        rls_mae=float(np.mean([abs(row['observed_count']-row['rls_prediction']) for row in trace])),trace=trace)
    root.with_name(root.name+'_shadow.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main(Path(sys.argv[1]))
