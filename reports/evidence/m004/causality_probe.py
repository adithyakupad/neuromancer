"""Full replay future-observation mutation fixture; synthetic copy, no new neurons."""
import json
from pathlib import Path
import shutil
import numpy as np
from replay import run_trial

source=Path('runs/m004-dev-01/n0_r32_STATIC');root=Path('runs/m004-causal-fixture');root.mkdir(exist_ok=False)
original=root/'original';altered=root/'altered';output=root/'output';output.mkdir()
for dest in (original,altered):
    dest.mkdir();shutil.copy2(source/'plans.npz',dest/'plans.npz')
    with np.load(source/'public.npz') as f:d={k:f[k].copy() for k in f.files}
    if dest==altered:d['rates'][3300:]+=20 # Explicit artificial future observation, not a scientific trial.
    np.savez_compressed(dest/'public.npz',**d)
    run_trial(dest,output)
a=np.load(output/'original/online.npz');b=np.load(output/'altered/online.npz')
np.testing.assert_array_equal(a['rolling'][:,:28],b['rolling'][:,:28]) # Origins39..66, forecasts before changed data arrive.
np.testing.assert_array_equal(a['theta'][:,:28],b['theta'][:,:28])
np.testing.assert_array_equal(a['one_step'][:,:1351],b['one_step'][:,:1351]) # Through prediction for bin starting66s.
np.testing.assert_array_equal(a['detector'][:,:27],b['detector'][:,:27])
result=dict(status='PASS',synthetic_fixture=True,mutation_start_s=66,unchanged_rolling_origins=28,
            unchanged_next_step_predictions_per_model=1351,no_new_neural_acquisition=True)
Path('reports/evidence/m004/causality_probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
