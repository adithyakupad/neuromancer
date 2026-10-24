from dataclasses import replace
import numpy as np
import pytest
from neuromancer.control import ControlCalibration, Policy, calibrate, project, feedback_step
from neuromancer.observation import Observation


def cal():
    return ControlCalibration(10., .25, .02, 50., 11., (0., .6, 1.2, 1.8, 2.4), True, 'valid')


def obs(start, count=1, trial='fixture'):
    #16 E recording channels,5cells each; count1 gives10Hz.
    return Observation(trial, start, start+20000, start+20000, (count,)*20, (0.,)*20,
                       (20000,)*20, (True,)*20, (), (), (0.,)*4, (0.,)*4, True)


def test_projection_arbitrary_transitions_kkt():
    rng = np.random.default_rng(22); previous = np.array([120., 120., 0., 0.])
    for _ in range(200):
        request = rng.uniform(-150., 250., 4)
        result, _ = project(request, previous)
        low, high = np.maximum(previous-30, 0), np.minimum(previous+30, 120)
        assert np.all(result >= low) and np.all(result <= high) and result.sum() <= 240
        free = (result > low+1e-8)&(result < high-1e-8)
        if free.sum() > 1: assert np.ptp((request-result)[free]) < 1e-8
        for _ in range(5):
            alternative, _ = project(rng.uniform(0,120,4), previous)
            assert (request-result)@(alternative-result) <= 1e-7
        previous = result
    p = np.array([120.,120.,0.,0.])
    for _ in range(4): p, _ = project([0,0,120,120], p)
    np.testing.assert_array_equal(p,[0,0,120,120])
    np.testing.assert_array_equal(project([np.nan]*4,p)[0],[0,0,90,90])
    with pytest.raises(ValueError): project([0]*4,[120]*4)


def test_aggregation_timing_no_gain_and_future():
    p = Policy(cal(), 'PI20_10')
    for k in range(49):
        p.accept(obs(51000000+k*20000),51020000+k*20000)
        np.testing.assert_array_equal(p.desired(),[50,0,50,0])
    p.accept(obs(51980000),52000000)
    assert p.last_error == 1 and p.integral == 10 and p.q == 80
    with pytest.raises(ValueError): p.accept(obs(52020000),52020000)
    with pytest.raises(ValueError): p.accept(obs(51980000),52000000)
    assert not hasattr(p,'gain') and not hasattr(p,'engine') and not hasattr(p,'network')


def test_antiwindup_saturation_and_release():
    p = Policy(cal(),'PI30_15',aggregate_bins=1)
    for k in range(100): p.accept(obs(51000000+k*20000,0),51020000+k*20000)
    assert p.q == 120 and p.integral == 0 and p.blocked and p.saturated
    p.accept(obs(53000000,2),53020000)
    assert p.q == 0 and p.integral == 0
    p.accept(obs(53020000,1),53040000)
    assert p.q == pytest.approx(80.3)


def test_missing_delayed_invalid_and_rearm():
    p = Policy(cal(),'PI20_10',aggregate_bins=2)
    p.accept(obs(51000000),51020000)
    p.missing(51040000)
    assert p.integral == 0 and not p.desired().any() and len(p.samples)==0
    for k in range(4): p.accept(obs(51040000+k*20000),51060000+k*20000)
    assert not p.safe and len(p.samples) == 0
    p.accept(obs(51120000),51140000); p.accept(obs(51140000),51160000)
    assert p.updates == 1
    p.accept(obs(51100000),51180000) # delayed completed observation
    assert p.safe and not p.desired().any()
    p.accept(replace(obs(51180000),counts=(-1,)*20),51200000)
    assert p.safe
    with pytest.raises(ValueError): p.accept(obs(51200000,trial='other'),51220000)


def test_future_mutation_and_independent_memory():
    first = Policy(cal(),'PI10_5',aggregate_bins=5); second = Policy(cal(),'PI10_5',aggregate_bins=5)
    prefix=[]
    for k in range(20):
        first.accept(obs(51000000+k*20000,k%3),51020000+k*20000)
        second.accept(obs(51000000+k*20000,k%3),51020000+k*20000)
        prefix.append(first.desired().copy()); np.testing.assert_array_equal(first.desired(),second.desired())
    for k in range(20,30): second.accept(obs(51000000+k*20000,9),51020000+k*20000)
    np.testing.assert_array_equal(first.desired(),prefix[-1]); assert first.expected_us != second.expected_us


def test_observation_before_subsequent_action_fake_trial():
    class Fake:
        time_us=51000000
        metadata={'trial_id':'fixture'}
        def advance(self,command,stop_us):
            from neuromancer.substrate import Receipt, StepResult
            assert command.start_us == self.time_us
            o=obs(self.time_us); self.time_us=stop_us
            return StepResult(o,Receipt('fixture',command.command_id,command.start_us,command.start_us,
                                       stop_us,command.current_pA,command.current_pA,'delivered',''),0,0)
    p=Policy(cal(),'PI20_10',aggregate_bins=1); f=Fake()
    a,_=feedback_step(f,p,np.zeros(4)); assert a.receipt.delivered_current_pA==(30.,0.,30.,0.)
    b,_=feedback_step(f,p,np.array(a.receipt.delivered_current_pA)); assert b.receipt.delivered_current_pA==(60.,0.,60.,0.)
    assert p.updates==2


def test_neural_tick_replay_isolation_and_receipts():
    from neuromancer._brian import BrianEngine
    from neuromancer.substrate import Config
    from neuromancer.diagnostic import schedule
    e=BrianEngine(Config(network_id=0,replicate_id=44,trial_id='test-control'))
    try:
        e.run_commands(schedule(e,np.zeros((50,4))))
        e.save('origin')
        # Start at1s for a bounded software fixture, not a scientific baseline.
        results=[]
        for _ in range(2):
            e.restore('origin'); p=Policy(cal(),'PI20_10',aggregate_bins=2,start_us=1000000)
            r=[]
            for k in range(8):
                from neuromancer.substrate import Command
                u,_=project(p.desired(),e.previous)
                z=e.advance(Command(e.config.trial_id,f't{k}',e.time_us,tuple(map(float,u))),e.time_us+20000)
                p.accept(z.observation,e.time_us); r.append((z.observation.counts,z.receipt.delivered_current_pA))
            results.append(r)
        assert results[0]==results[1]
        assert results[0][0][1]==(30.,0.,30.,0.)
        e.restore('origin')
        batch=e.run_commands(schedule(e,[u for _,u in results[0]]))
        assert [(z.observation.counts,z.receipt.delivered_current_pA) for z in batch]==results[0]
    finally: e.close()


def test_calibration_exact_math_and_future_rejection():
    # Synthetic declared prefix; no neural acquisition.
    from neuromancer.calibration import prefix_schedule
    from neuromancer.substrate import Receipt
    os=[]; rs=[]
    rows=prefix_schedule()
    for k in range(2350):
        o=obs(k*20000); counts=np.ones(20,dtype=int)
        for j in range(4):
            if 1000+400*j<=k<1150+400*j:
                counts[:]=(j+2)
        os.append(replace(o,counts=tuple(map(int,counts))))
        u=tuple(rows[k]); rs.append(Receipt('fixture',str(k),k*20000,k*20000,(k+1)*20000,u,u,'delivered',''))
    c=calibrate(os,rs)
    assert c.baseline_hz==10 and c.target_hz==11
    assert c.slope_hz_per_pA==pytest.approx(1/3) and c.feedforward_pA==pytest.approx(3)
    assert c.valid and c.noise_hz==0
    with pytest.raises(ValueError): calibrate(os+[obs(47000000)],rs)


def test_network_replication_and_mean_gate():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).parents[1]/'reports/evidence/m005a/analyze.py'
    spec=importlib.util.spec_from_file_location('m005a_statistics',path);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    rows=[]
    for n in range(10):
        for r in (41,42):
            for cond in ('STATIC','LOSS'):
                for name,rate,mae in [('ZERO',10.,1.),('MAX',11.5,.5),('FIXED',10.6,.4),('PI20_10',10.9,.2)]:
                    for window in ('stationary','late'):
                        rows.append(dict(network=n,replicate=r,condition=cond,controller=name,window=window,
                                         rate_hz=rate,mae_hz=mae,bias_hz=-.1,noise_hz=.25,baseline_hz=10.,
                                         calibration_valid=True,fallback_decisions=0))
    gates=a.network_gates(rows,'PI20_10')
    assert len(gates)==20 and all(g['qualified'] for g in gates)
    import json
    json.dumps(gates,allow_nan=False)
    duplicated=a.network_gates(rows+rows,'PI20_10')
    assert gates==duplicated
    assert a.ci(np.ones(10))==[1.,1.]


def test_projection_strict_floating_point_slew_contract():
    rng=np.random.default_rng(280)
    for _ in range(5000):
        p=rng.uniform(0,120,4);p*=min(1.,240/p.sum())
        while p.sum()>240: p=np.nextafter(p,np.zeros(4))
        # Opposite corners force subtraction/addition at the exact slew edge.
        request=rng.choice([0.,120.],4)
        u,_=project(request,p)
        assert np.all(abs(u-p)<=30.),(p,request,u,abs(u-p))
        assert u.sum()<=240
