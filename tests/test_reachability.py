"""M002.2 adds finite-bank evidence without changing the neural model."""
import numpy as np
import pytest
from neuromancer.reachability import intervention_bank,audit_actions,EXPECTED_EXPOSURE


def test_bank_constraints_and_exact_charge_matches():
    desired,actual=intervention_bank()
    assert actual.shape==desired.shape==(12,300,4)
    for a,rows in enumerate(actual):
        check=audit_actions(rows)
        assert check['constraint_violations']==0
        assert check['total_exposure_pA_s']==pytest.approx(EXPECTED_EXPOSURE[a])
    for dynamic,constant in [(9,3),(10,8),(11,1)]:
        assert actual[dynamic].sum()==pytest.approx(actual[constant].sum())
    np.testing.assert_array_equal(actual[11,8],[0]*4)
    np.testing.assert_array_equal(actual[9,26],[0]*4)
    assert np.allclose(actual[10,3:].sum(axis=-1),240)
    bad=actual[4].copy();bad[0]=60
    assert audit_actions(bad)['constraint_violations']>0
    with pytest.raises(ValueError):audit_actions(np.full((300,4),np.nan))
