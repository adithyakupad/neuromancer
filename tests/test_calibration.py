"""Software fixtures only: no new neural outcomes used to choose this protocol."""
from dataclasses import replace
import inspect
import numpy as np
import pytest
from neuromancer.calibration import fit,inverse,prefix_schedule,ramp
from neuromancer.observation import Observation
from neuromancer.substrate import Receipt


def fixture():
    rows=prefix_schedule();observations=[];receipts=[]
    for k,row in enumerate(rows[:2350]):
        rate=10+row[0]/30
        #16 observed E channels x5 cells; these synthetic integer counts make h=(0,10,20,30,40)Hz.
        count=int(round(rate));counts=tuple(count if j%5<4 else 0 for j in range(20))
        observations.append(Observation('fixture',k*20000,(k+1)*20000,(k+1)*20000,counts,(0.,)*20,
            (20000,)*20,(True,)*20,(),(),(0.,)*4,(0.,)*4,True))
        receipts.append(Receipt('fixture',str(k),k*20000,k*20000,(k+1)*20000,tuple(row),tuple(row),'delivered',''))
    return tuple(observations),tuple(receipts)


def test_exact_prefix_target_math_and_blind_inverse():
    obs,receipts=fixture();result=fit(obs,receipts)
    assert result.h_hz==pytest.approx((0,10,20,30,40))
    assert result.baseline_hz==100 and result.targets_hz==pytest.approx((102.4,121.6))
    assert result.span_hz==pytest.approx(19.2)
    assert result.lookup_pA==pytest.approx((7.2,64.8)) and result.valid
    assert tuple(inspect.signature(fit).parameters)==('observations','receipts')
    assert tuple(inspect.signature(inverse).parameters)==('h','excursion')
    source=inspect.getsource(inspect.getmodule(fit))
    assert '._brian' not in source and 'connectivity' not in source and 'efficacy' not in source
    #Non-count derived rates and filter values carry no influence on the raw-count calibration.
    changed=tuple(replace(o,rates_hz=(999.,)*20,sector_rate_hz=(999.,)*4,filtered_sector_rate_hz=(999.,)*4) for o in obs)
    assert fit(changed,receipts)==result
    with pytest.raises(TypeError):fit(obs,receipts,gain=.6)


def test_causal_inputs_and_test_data_separation():
    obs,receipts=fixture()
    with pytest.raises(ValueError):fit(obs+(obs[-1],),receipts+(receipts[-1],))
    for bad in [replace(obs[-1],available_us=47_000_001),replace(obs[-1],valid=(False,)*20),
                replace(obs[-1],coverage_us=(0,)*20),replace(obs[-1],counts=(-1,)*20)]:
        with pytest.raises(ValueError):fit(obs[:-1]+(bad,),receipts)
    bad=replace(receipts[-1],delivered_current_pA=(0.,)*4)
    with pytest.raises(ValueError):fit(obs,receipts[:-1]+(bad,))
    #All-late counts are excluded from the API, never trusted as extra calibration.
    assert fit(obs,receipts).frozen_at_us==47_000_000


def test_monotonicity_unreachable_and_ill_conditioned_maps():
    for h in [(0,1,.9,2,3),(0,0,1,2,3),(0,1e-10,1,2,3),(0,1,2,3,np.nan)]:
        with pytest.raises(ValueError):inverse(h,.5)
    for target in (-.1,4.1,np.nan):
        with pytest.raises(ValueError):inverse((0,1,2,3,4),target)
    assert inverse((0,1,2,3,4),0)==0 and inverse((0,1,2,3,4),4)==120
    obs,receipts=fixture()
    flat=tuple(replace(o,counts=(10,)*20) for o in obs)
    result=fit(flat,receipts)
    assert not result.valid and result.lookup_pA is None and result.span_hz==0


def test_original_bounds_slew_and_prefix_budget():
    rows=prefix_schedule()
    assert rows.shape==(2550,4) and np.all(rows[:,[1,3]]==0)
    assert rows.min()>=0 and rows.max()<=120 and rows.sum(axis=1).max()<=240
    assert np.abs(np.diff(np.vstack([np.zeros(4),rows]),axis=0)).max()==30
    assert np.all(rows[-1]==0)
    #Up/down ramps balance across complete blocks;600pA total hold doses x4s.
    assert rows.sum()*.02==pytest.approx(2400)
    for desired in [np.full((300,4),121),np.full((300,4),61),np.full((300,4),np.nan)]:
        with pytest.raises(ValueError):ramp(desired)
    for q in (0,7.2,64.8,120):
        desired=np.zeros((300,4));desired[:,::2]=q;actual=ramp(desired)
        assert actual.sum()*.02<=12*q
        assert np.abs(np.diff(np.vstack([np.zeros(4),actual]),axis=0)).max()<=30


def analysis_module():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('m0023_analysis',Path(__file__).resolve().parents[1]/'reports/evidence/m002_3/analyze.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_network_gate_does_not_pool_bins_or_ignore_bad_replicates():
    a=analysis_module();base=np.full(5,13.);sector=np.full((5,4),13.)
    span=np.full(5,1.2);noise=np.full(5,.2);margin=np.full(5,.2);errors=np.full((5,2,2),.2);valid=np.ones(5,dtype=bool)
    assert a.gate(base,sector,span,noise,margin,errors,valid,True)['qualified']
    assert not a.gate(base,sector,span*.5,noise,margin,errors,valid,True)['qualified']
    errors[0,1,1]=.5
    assert not a.gate(base,sector,span,noise,margin,errors,valid,True)['components']['error_g0.6_H']
    errors[:]=.2;valid[-1]=False
    assert not a.gate(base,sector,span,noise,margin,errors,valid,True)['qualified']
    valid[:]=True;margin[:]=[.1,.1,.1,.1,-.1]
    assert not a.gate(base,sector,span,noise,margin,errors,valid,True)['components']['headroom']
    assert a.network_bootstrap(np.ones((10,2)))==dict(mean=[1,1],lower=[1,1],upper=[1,1])
    assert a.ci(np.full(5,2.))==dict(mean=2.,lower=2.,upper=2.)


def test_new_noise_ids_independent_and_network_parameters_fixed():
    from neuromancer._brian import stream,realization,digest
    from neuromancer.substrate import Config
    configs=[Config(network_id=0,replicate_id=r) for r in range(8,13)]
    assert len({digest(stream(c,4,block=51).normal(size=100)) for c in configs})==5
    identities=[{k:digest(v) for k,v in realization(c).items()} for c in configs]
    assert all(x==identities[0] for x in identities)


def test_execution_lineage_frozen_before_neural_run():
    import hashlib,json,subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    provenance=root/'runs/m002_3-calibration-01/provenance.json'
    if not provenance.exists():provenance=root/'reports/evidence/m002_3/results/raw_provenance.json'
    if not provenance.exists():pytest.skip('Scientific evidence not yet generated')
    record=json.loads(provenance.read_text())
    prereg=root/'reports/evidence/m002_3/PREREGISTRATION.md'
    assert record['preregistration_sha256']==hashlib.sha256(prereg.read_bytes()).hexdigest()
    for name,digest in record['source_hashes'].items():
        frozen = (root/'docs/history/BRIAN_V1_SNAPSHOT.py' if name=='neuromancer/_brian.py' else root/'src'/name)
        assert hashlib.sha256(frozen.read_bytes()).hexdigest()==digest
    old=json.loads((prereg.parent/'preservation.json').read_text())
    for name,digest in old['sha256'].items():
        # Release documentation may evolve; preserve and verify original bytes.
        frozen = (root/'docs/history/README_M002_SNAPSHOT.md' if name=='README.md'
                  else root/'docs/history/PYPROJECT_M002_3_SNAPSHOT.toml' if name=='pyproject.toml'
                  else root/'docs/history/BRIAN_V1_SNAPSHOT.py' if name=='src/neuromancer/_brian.py'
                  else root/name)
        assert hashlib.sha256(frozen.read_bytes()).hexdigest()==digest
    committed=subprocess.check_output(['git','show','HEAD:reports/evidence/m002_3/PREREGISTRATION.md'],cwd=root)
    assert committed==prereg.read_bytes()


def test_complete_analysis_records_all_invalid_trials(tmp_path):
    import json
    a=analysis_module();raw=tmp_path/'raw';raw.mkdir()
    for n in range(10):
        for rep in range(8,13):
            folder=raw/f'network_{n}_replicate_{rep}';folder.mkdir()
            np.savez_compressed(folder/'numerical.npz',prefix_counts=np.zeros((2550,20),dtype=np.int32),
                observed_counts=np.zeros((2,4,300,20),dtype=np.int32),
                filtered_sector_rates_hz=np.zeros((2,4,300,4)),delivered_current_pA=np.zeros((2,4,300,4)))
            trial=dict(status='complete',network_id=n,replicate_id=rep,calibration=dict(baseline_hz=0,
                targets_hz=[0,0],span_hz=0,valid=False,reason='flat',lookup_pA=None,h_hz=[0]*5),
                receipt_ledger=[dict(gain=g,name=name,constraint_violations=0,neural_ns=0,observation_ns=0) for g in (1.,.6) for name in ('S','C120','L','H')],
                engine=dict(initialization_ns=0),peak_rss_bytes=0,total_wall_ns=0)
            (folder/'trial.json').write_text(json.dumps(trial))
    (raw/'summary.json').write_text(json.dumps(dict(status='complete',wall_ns=0)))
    (raw/'provenance.json').write_text('{}')
    output=tmp_path/'analysis';a.main(raw,output)
    result=json.loads((output/'comparison.json').read_text())
    assert result['completed_branches']==400 and result['qualified_networks']==0
    assert result['calibration_invalid_count']==50 and result['scientific_qualification']=='HOLD'
    assert len((output/'calibration_trials.csv').read_text().splitlines())==51
    assert len((output/'confirmation_trials.csv').read_text().splitlines())==401
