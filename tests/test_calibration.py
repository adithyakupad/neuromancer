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
