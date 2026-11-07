from types import SimpleNamespace
import numpy as np
import pytest
from neuromancer.control import Policy,ControlCalibration
from neuromancer.extended_recovery import step_second,gain_for,BRANCHES
from neuromancer.recovery_metrics import regime_gate,cohort_gate,recovery_times,score
from neuromancer.observation import Observation
from neuromancer.substrate import Receipt,StepResult


def calibration():return ControlCalibration(10.,.25,.02,50.,11.,(0.,.6,1.2,1.8,2.4),True,'valid')


class Fake:
    def __init__(self):
        self.time_us=51_000_000;self.previous=np.zeros(4);self.config=SimpleNamespace(trial_id='extended-fixture');self.group=SimpleNamespace(gain=1.);self.records=[]
    def run_commands(self,commands):
        out=[]
        for c in commands:
            start=self.time_us;assert c.start_us==start;u=np.array(c.current_pA);assert (abs(u-self.previous)<=30).all() and u.sum()<=240 and (u>=0).all() and (u<=120).all()
            self.previous=u;self.time_us+=20000;self.records.append((start,self.group.gain,tuple(u)))
            o=Observation(self.config.trial_id,start,self.time_us,self.time_us,(1,)*20,(0.,)*20,(20000,)*20,(True,)*20,(),(),(0.,)*4,(0.,)*4,True)
            out.append(StepResult(o,Receipt(self.config.trial_id,c.command_id,start,start,self.time_us,c.current_pA,c.current_pA,'delivered',''),0,0))
        return out


def test_continuous64_equals32_plus32_no_reset():
    runs=[]
    for sections in ((64,),(32,32)):
        engine=Fake();p=Policy(calibration(),'PI10_5');states=[]
        for length in sections:
            for _ in range(length):
                part,u,state,_=step_second(engine,p,'LOSS');states.append(state);assert len(part)==50
        runs.append((engine.records,np.array(states),p.record()))
        assert engine.time_us==115_000_000 and p.updates==64 and p.expected_us==115_000_000
    assert runs[0][0]==runs[1][0];np.testing.assert_array_equal(runs[0][1],runs[1][1]);np.testing.assert_array_equal(runs[0][2],runs[1][2])
    assert runs[0][1][32,7]==32 and runs[0][1][32,2]!=0
    for i in (15,16,31,32,63):assert runs[0][1][i,0]==51_000_000+i*1_000_000
    assert runs[0][0][799][1]==1 and runs[0][0][800][1]==.6
    with pytest.raises(ValueError):step_second(engine,p,'LOSS')


@pytest.mark.parametrize('condition,second,value',[('STATIC',63,1.),('LOSS',15,1.),('LOSS',16,.6),('LOSS',32,.6)])
def test_exact_gain_boundary(condition,second,value):assert gain_for(condition,second)==value


@pytest.mark.parametrize('condition,second',[('bad',1),('LOSS',-1),('LOSS',64)])
def test_invalid_phase(condition,second):
    with pytest.raises(ValueError):gain_for(condition,second)


def test_phase_mismatch_and_causal_first_action():
    f=Fake();p=Policy(calibration(),'PI10_5');a,u,state,_=step_second(f,p,'LOSS');assert state[1]==50 and state[2]==0 and p.integral==5
    assert f.records[0][2]==(30.,0.,30.,0.)
    f.time_us+=20000
    with pytest.raises(ValueError):step_second(f,p,'LOSS')
    assert not hasattr(p,'gain') and not hasattr(p,'engine')


def pair(errors):return [dict(network=0,replicate=k,errors=errors,calibration_valid=True,baseline_hz=10.,noise_hz=.25,max_target_margin_hz=.5,fallbacks=0,violations=0) for k in (45,46)]


def test_persistent_good_gate_and_transient_crossing_fail():
    assert regime_gate(pair(np.full(64,.1)),'LOSS')['qualified']
    x=np.full(64,-.4);x[60]=0;assert not regime_gate(pair(x),'LOSS')['qualified']
    x=np.zeros(64);x[48:56]=.3;x[56:]=-.3;g=regime_gate(pair(x),'LOSS');assert abs(g['bias_hz'])<1e-12 and not g['components']['block_bias'] and not g['qualified']


def test_repeat_separation_invalidity_and_headroom():
    p=pair(np.zeros(64))
    with pytest.raises(ValueError):regime_gate(p[:1],'LOSS')
    p[1]['replicate']=45
    with pytest.raises(ValueError):regime_gate(p,'LOSS')
    p=pair(np.zeros(64));p[0]['fallbacks']=1;assert not regime_gate(p,'LOSS')['qualified']
    p=pair(np.zeros(64));p[0]['max_target_margin_hz']=-.2;assert not regime_gate(p,'LOSS')['qualified'] and regime_gate(p,'STATIC')['qualified']
    with pytest.raises(ValueError):score(np.full(64,np.nan),(48,64))


def test_network_gate_not_bins_or_repeats():
    good=regime_gate(pair(np.full(64,.1)),'LOSS');assert cohort_gate([good]*10)['pass_gate']
    bad=dict(good,qualified=False);assert not cohort_gate([good]*7+[bad]*3)['pass_gate']
    with pytest.raises(ValueError):cohort_gate([good]*20)
    assert not cohort_gate([dict(good,bias_hz=.3)]*10)['pass_gate']


def test_recovery_descriptor_persistence_not_single_crossing():
    x=np.full(64,-.5);x[16]=0;assert recovery_times(x)['settling_censored']
    x[32:]=.1;r=recovery_times(x);assert r['settling_delay_s']>=16 and not r['settling_censored']
    assert len(BRANCHES)==5 and ('STATIC','MAX') not in BRANCHES
