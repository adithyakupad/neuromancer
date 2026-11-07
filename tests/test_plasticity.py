import numpy as np
import pytest
from neuromancer.plasticity import Eligibility, decay, reward_update, PlasticReservoir
from neuromancer.substrate import Config, Command
from dataclasses import fields


def assert_observations_equal(left, right):
    for actual, expected in zip(left, right, strict=True):
        for field in fields(actual.observation):
            np.testing.assert_array_equal(getattr(actual.observation, field.name),
                                          getattr(expected.observation, field.name))


def test_pair_rule_and_simultaneous():
    positive = Eligibility()
    positive.event(0, pre=True)
    assert positive.event(10, post=True) == pytest.approx(np.exp(-.5))
    negative = Eligibility()
    negative.event(0, post=True)
    assert negative.event(10, pre=True) == pytest.approx(-np.exp(-.5))
    simultaneous = Eligibility()
    assert simultaneous.event(1, pre=True, post=True) == 1.
    assert positive.event(210) == pytest.approx(np.exp(-1.5))


def test_rewards_bounds_finite_and_no_mutation():
    weights = np.array([15., 15.])
    eligibility = np.array([[1., -1.]])
    np.testing.assert_array_equal(reward_update(weights, eligibility, [1], enabled=True), [15.1,14.9])
    np.testing.assert_array_equal(reward_update(weights, eligibility, [-1], enabled=True), [14.9,15.1])
    for enabled,reward in [(False,1),(True,0)]:
        np.testing.assert_array_equal(reward_update(weights,eligibility,[reward],enabled=enabled),weights)
    np.testing.assert_array_equal(reward_update(weights,eligibility*1e8,[1],enabled=True),[30,0])
    np.testing.assert_array_equal(weights,[15,15])
    with pytest.raises(ValueError):
        reward_update(weights, [[np.nan,0]], [1], enabled=True)


def test_reference_checkpoint():
    trace = Eligibility()
    trace.event(0, pre=True)
    state = trace.checkpoint()
    expected = trace.event(10, post=True)
    trace.restore(state)
    assert trace.event(10, post=True) == expected
    with pytest.raises(ValueError):
        decay(1,-1,20)


def test_actual_network_disabled_replay_and_restoration():
    from neuromancer._brian import BrianEngine
    config = Config(network_id=13000,replicate_id=1300,root_seed=20261104,trial_id='mechanism')
    original = BrianEngine(config)
    plastic = PlasticReservoir(config)
    commands = [Command('mechanism',str(i),i*20000,(0.,0.,0.,0.)) for i in range(5)]
    try:
        expected = original.run_commands(commands)
        initial_weights = plastic.weights()
        actual = plastic.engine.run_commands(commands)
        assert_observations_equal(actual, expected)
        traces = plastic.eligibility()
        assert np.all(np.isfinite(traces))
        plastic.learn([traces],[1])
        np.testing.assert_array_equal(plastic.weights(),initial_weights)
        plastic.restore('plastic_initial')
        replay = plastic.engine.run_commands(commands)
        assert_observations_equal(replay, actual)
        np.testing.assert_array_equal(plastic.eligibility(),traces)
        plastic.enabled=True
        plastic.learn([traces],[1])
        plastic.restore('plastic_initial')
        np.testing.assert_array_equal(plastic.weights(),initial_weights)
    finally:
        original.close()
        plastic.close()


@pytest.mark.parametrize('pre_ms,post_ms',[(0,10),(10,0),(0,0),(0,.1)])
def test_brian_pair_matches_independent_arithmetic(pre_ms,post_ms):
    import brian2 as b
    from neuromancer.plasticity import TRACE_MODEL,PRE_RULE,POST_RULE
    from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
    clock=b.Clock(dt=.1*b.ms)
    pre=b.SpikeGeneratorGroup(1,[0],[pre_ms]*b.ms,clock=clock)
    post=b.SpikeGeneratorGroup(1,[0],[post_ms]*b.ms,clock=clock)
    syn=b.Synapses(pre,post,TRACE_MODEL,on_pre=PRE_RULE,on_post=POST_RULE,
                   clock=clock,codeobj_class=NumpyCodeObject)
    syn.connect()
    net=b.Network(pre,post,syn)
    net.run(30*b.ms)
    actual=float(syn.eligibility[0])*np.exp(-float((net.t-syn.lastupdate[0])/b.ms)/200)
    if pre_ms<=post_ms:
        expected=np.exp(-(post_ms-pre_ms)/20)*np.exp(-(30-post_ms)/200)
    else:
        expected=-np.exp(-(pre_ms-post_ms)/20)*np.exp(-(30-pre_ms)/200)
    assert actual==pytest.approx(expected,rel=1e-12)
