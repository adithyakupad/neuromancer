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
