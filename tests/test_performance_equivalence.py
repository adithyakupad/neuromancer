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
