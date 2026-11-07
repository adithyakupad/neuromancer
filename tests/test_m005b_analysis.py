import numpy as np
import pytest
from neuromancer.m005b_analysis import interval,superiority


def test_frozen_primary_thresholds_and_both_comparators():
 pi=np.full(10,12.);adaptive=np.full(10,10.5);fixed=np.full(10,10.6)
 assert superiority(pi,adaptive,.10,1.2)['pass_gate']
 assert not superiority(fixed,adaptive,.05,.6)['pass_gate']
 assert not superiority(pi,pi-.1,.10,1.2)['pass_gate']
 uncertain=superiority(np.full(10,10.),np.full(10,10.)-np.r_[np.full(8,3.),np.full(2,-5.)],.10,1.2)
 assert uncertain['decision']=='HOLD' and uncertain['positive_networks']==8


def test_network_replication_and_floor_are_explicit():
 with pytest.raises(ValueError):interval(np.zeros(20))
 assert interval(np.ones(5))['ci95']==[1.,1.]
 g=superiority(np.zeros(10),np.ones(10),.10,1.2)
 assert g['denominator_floor_count']==10 and not g['pass_gate']
