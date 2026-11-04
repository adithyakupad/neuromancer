"""Performance variants retain exact frozen V1 numerical operations."""
import hashlib
import numpy as np
import pytest
from neuromancer._brian import digest

@pytest.mark.parametrize('array',[np.array(3.),np.arange(20)[::2],np.empty((0,4)),np.ones((3,2),order='F'),np.array(['ab','cd']),np.array([object()],dtype=object)])
def test_streamed_digest_matches_original_payload(array):
    v=np.ascontiguousarray(array)
    expected=hashlib.sha256(str(v.dtype).encode()+str(v.shape).encode()+v.tobytes()).hexdigest()
    assert digest(array)==expected

@pytest.mark.parametrize('replicate,block',[(0,0),(1,1)])
def test_noise_operations_match_original_bit_for_bit(replicate,block):
    import math
    from neuromancer._brian import stream,innovations
    from neuromancer.substrate import Config
    config=Config(replicate_id=replicate)
    fine=stream(config,4,block=block).standard_normal((20000,1000))
    a=math.exp(-.05/5)
    expected=(a*fine[::2]+fine[1::2])/math.sqrt(1+a*a)
    actual,fine_hash=innovations(config,block)
    np.testing.assert_array_equal(actual,expected)
    assert fine_hash==digest(fine)

def reference_planner():
    import types
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'docs/history/PLANNER_V1_SNAPSHOT.py'
    module=types.ModuleType('neuromancer._v1_planner_reference');module.__package__='neuromancer'
    exec(compile(p.read_text(),str(p),'exec'),module.__dict__)
    return module

@pytest.mark.parametrize('previous',[0.,np.nextafter(30.,0.),np.nextafter(30.,120.),37.3,60.,119.99999999999999,120.])
def test_bank_ramp_and_all625_candidates_exactly_equal_v1(previous):
    from neuromancer.predictive_planner import bank
    a=bank(previous);b=reference_planner().bank(previous)
    for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
    a[2][0,0]=-999
    assert bank(previous)[2][0,0]>=0 # no shared mutable output cache


def test_all_candidate_scores_predictions_and_action_ties_equal_v1():
    from neuromancer.predictive_planner import plan
    old=reference_planner();rng=np.random.default_rng(20261106)
    rec=dict(mean=np.full(40,20.),scale=np.full(40,10.),output_mean=np.full(4,8.))
    for i in range(25):
        theta=rng.normal(0,.002,(41,4));h=np.zeros((9,4));h[:,::2]=i*5
        for th in (theta,np.zeros((41,4))):
            a=plan(rec,th,h,9.,51_000_000,limit_s=10);b=old.plan(rec,th,h,9.,51_000_000,limit_s=10)
            for name in a:
                if name!='elapsed_ns':np.testing.assert_array_equal(a[name],b[name],err_msg=name)
