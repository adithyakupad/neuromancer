"""Frozen cohort and compact state encoding contracts; no science acquisition."""
import numpy as np
import pytest
from neuromancer.m005b_study import jobs,BANK,worker
from neuromancer.research_codec import model_digest,compact_plan
from types import SimpleNamespace


def test_frozen_cohorts_and_reference_bank():
 assert jobs('primary')==[(n,r) for n in range(10) for r in (47,48)]
 assert jobs('validation')==[(n,r) for n in range(10,15) for r in (49,50)]
 assert jobs('faults')==[(n,49) for n in range(3)] and jobs('engineering')==[(0,60)]
 assert len(BANK)==13 and BANK[-1]==('LOSS','MAX')
 with pytest.raises(ValueError):jobs('unknown')
 with pytest.raises(ValueError):worker(100,47,'primary','unused')


def test_model_digest_preserves_every_coefficient_and_information_value():
 m=SimpleNamespace(theta=np.zeros((41,4)),p=np.eye(41),bias_p=.1);a=model_digest(m);m.theta[40,3]=1;assert model_digest(m)!=a
 m.theta[40,3]=0;m.p[40,40]=2;assert model_digest(m)!=a


def test_reference_timing_wrapper_preserves_original_actions_and_states():
 from test_predictive import fixture,observation,receipt
 from neuromancer.m005b_study import make_controller
 from neuromancer.predictive import PIReference
 init,*_=fixture();a=make_controller(init,'PI10_5');b=PIReference(init.calibration,init.trial_id,init.history[-1])
 for i in range(100):
  t=51_000_000+i*20000;x=a.command(t);y=b.command(t);assert x==y
  for c,cmd in ((a,x),(b,y)):c.accept(observation(t),receipt(cmd),t+20000)
  np.testing.assert_array_equal(a.policy.record(),b.policy.record())
 assert len(a.command_ns)==len(a.update_ns)==100
