"""New diagnostic contracts; all original M002 tests remain unchanged."""
import numpy as np
import pytest
from neuromancer.authority_diagnosis import TARGETS,NAMES,action_schedule,action_audit,evaluator_groups
from neuromancer._brian import realization
from neuromancer import Config


def test_frozen_bank_and_ramp_exposure():
    assert len(NAMES)==8 and len(set(map(tuple,TARGETS)))==8
    np.testing.assert_array_equal(TARGETS[0],[0,0,0,0])
    for name,target in zip(NAMES,TARGETS):
        rows=action_schedule(target);audit=action_audit(rows)
        assert audit['constraint_violations']==0
        if name=='S':assert audit['total_exposure_pA_s']==0
        elif name=='D':
            np.testing.assert_array_equal(rows[0],[30]*4)
            assert audit['total_exposure_pA_s']==pytest.approx(1197.6)
        else:
            active=target>0
            np.testing.assert_array_equal(rows[:4,active],np.array([[30,30],[60,60],[90,90],[120,120]]))
            assert audit['total_exposure_pA_s']==pytest.approx(1192.8)
        if name!='S':assert audit['post_ramp_exposure_pA_s']==pytest.approx(1185.6)
    bad=action_schedule(TARGETS[1]);bad[0]=[31]*4
    assert action_audit(bad)['constraint_violations']>0


def test_fixed_evaluator_memberships_do_not_change_observable():
    p=realization(Config());g=evaluator_groups(p)
    assert len(g['observed_E'])==80 and len(g['fixed_unstim_E'])==600
    assert np.isin(g['observed_E'],g['fixed_unstim_E']).all()
    assert not np.intersect1d(g['fixed_unstim_E'],p['stimulation']).size
    for j in range(4):
        assert len(g[f'fixed_unstim_sector_{j}'])==150
        assert len(g[f'observed_sector_{j}'])==20
