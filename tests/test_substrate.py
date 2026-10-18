"""Instrument qualification: no fitted models or controllers."""
from dataclasses import asdict, fields, replace
import math
import numpy as np
import pytest
import brian2 as b
from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
from neuromancer import Config, Command, Trial, StepResult
from neuromancer._brian import BrianEngine, realization, innovations, digest
from neuromancer.observation import bin_events, RateFilter


def commands(engine, values):
    return [Command(engine.config.trial_id, f'c{engine.time_us+i*20000}',
                    engine.time_us+i*20000, tuple(map(float, row)))
            for i, row in enumerate(values)]


def observations_equal(left, right):
    assert len(left) == len(right)
    for a, c in zip(left, right):
        assert a.receipt == c.receipt
        for field in fields(a.observation):
            x, y = getattr(a.observation, field.name), getattr(c.observation, field.name)
            if isinstance(x, tuple):
                np.testing.assert_array_equal(x, y)
            else:
                assert x == y


def responsive_fixture(efficacy=1):
    """Explicit deterministic fixture, not a changed V0 network or authority result."""
    engine = BrianEngine(Config(efficacy=efficacy, retain_spikes=True))
    engine.group.namespace['background'] = 149*b.pA
    engine.group.namespace['noise_sigma'] = 0*b.pA
    engine.group.tau_m = 20*b.ms
    engine.group.v = -65*b.mV
    engine.group.eta = 0*b.pA
    for syn in engine.synapses:
        syn.weight = 0*b.pA
    p = engine.parameters
    candidates = ((p['pre'] < 800)
                  & np.isin(p['pre'], p['stimulation'].ravel())
                  & np.isin(p['post'], p['recording'][:, :].ravel()))
    edge = np.flatnonzero(candidates)[0]
    source, target = p['pre'][edge], p['post'][edge]
    exc_edge = int(np.sum(p['pre'][:edge] < 800))
    engine.synapses[0].weight[exc_edge] = 1000*b.pA
    engine.group.v[[source, target]] = -50.01*b.mV
    channel = int(np.where(np.any(p['stimulation'] == source, axis=1))[0][0])
    engine.save('fixture')
    return engine, int(source), int(target), channel, int(p['delay_us'][edge])


def test_frozen_distributions_memberships_and_parameter_roles():
    p = realization(Config())
    same = realization(Config(replicate_id=2))
    other = realization(Config(network_id=1))
    for key in p:
        np.testing.assert_array_equal(p[key], same[key])
    assert digest(p['pre']) != digest(other['pre'])
    assert np.all(p['pre'] != p['post'])
    assert len(set(zip(p['pre'], p['post']))) == len(p['pre'])
    assert 47000 < len(p['pre']) < 53000
    assert np.all((p['tau_ms'] >= 18) & (p['tau_ms'] < 22))
    assert np.all((p['initial_mV'] >= -65) & (p['initial_mV'] < -50))
    exc = p['pre'] < 800
    assert np.all((p['weight_pA'][exc] >= 12) & (p['weight_pA'][exc] < 18))
    assert np.all((p['weight_pA'][~exc] >= -72) & (p['weight_pA'][~exc] < -48))
    assert set(p['delay_us']) == set(range(1000, 2001, 100))
    assert p['stimulation'].shape == (4, 50) and p['recording'].shape == (20, 5)
    assert len(np.unique(p['recording'])) == 100
    assert len(np.unique(p['stimulation'])) == 200
    assert not np.intersect1d(p['recording'], p['stimulation']).size
    for sector in range(4):
        assert np.all(p['stimulation'][sector] // 200 == sector)
        assert np.all(p['recording'][sector*5:sector*5+4] // 200 == sector)
        assert np.all((p['recording'][sector*5+4]-800) // 50 == sector)


def test_noise_roles_block_independence_and_nested_ou():
    coarse, h = innovations(Config(), 0)
    again, h2 = innovations(Config(efficacy=0), 0)
    np.testing.assert_array_equal(coarse, again)
    assert h == h2
    fine, fine_hash = innovations(Config(dt_us=50), 0)
    a = math.exp(-.05/5)
    np.testing.assert_array_equal(coarse, (a*fine[::2]+fine[1::2])/math.sqrt(1+a*a))
    assert fine_hash == h
    _, replica_hash = innovations(Config(replicate_id=1), 0)
    _, block_hash = innovations(Config(), 1)
    assert len({h, replica_hash, block_hash}) == 3


def test_continuous_chunked_reset_and_cross_block_replay():
    engine = BrianEngine(Config(retain_spikes=True))
    rows = np.tile(np.array([[30.,30.,30.,30.], [60.,60.,60.,60.],
                             [30.,30.,30.,30.], [0.,0.,0.,0.]]), (14,1))
    schedule = commands(engine, rows)
    continuous = engine.run_commands(schedule)
    voltage = np.asarray(engine.group.v).copy()
    eta = np.asarray(engine.group.eta).copy()
    spikes = np.asarray(engine.monitor.t/b.us).copy()
    hashes = dict(engine.noise_hashes)
    engine.reset()
    chunked = engine.run_commands(schedule, chunked=True)
    observations_equal(continuous, chunked)
    np.testing.assert_array_equal(voltage, np.asarray(engine.group.v))
    np.testing.assert_array_equal(eta, np.asarray(engine.group.eta))
    np.testing.assert_array_equal(spikes, np.asarray(engine.monitor.t/b.us))
    assert hashes == engine.noise_hashes and len(hashes) == 2
    # Snapshot mid-episode restores refractory/delay state, filter and cursors.
    engine.save('mid')
    more = commands(engine, [(0.,)*4]*3)
    expected = engine.run_commands(more)
    engine.restore('mid')
    observations_equal(expected, engine.run_commands(more, chunked=True))


def test_causal_responsive_fixture_and_zero_coupling():
    for efficacy in (1., 0.):
        engine, source, target, channel, delay = responsive_fixture(efficacy)
        row = np.zeros(4); row[channel] = 30
        stim = engine.advance(commands(engine, [row])[0], 20000)
        times = np.rint(np.asarray(engine.monitor.t/b.us)).astype(int)
        neurons = np.asarray(engine.monitor.i)
        engine.restore('fixture')
        sham = engine.advance(commands(engine, [(0.,)*4])[0], 20000)
        if efficacy == 1:
            assert sum(stim.observation.counts) > sum(sham.observation.counts)
            source_time = times[neurons == source][0]
            target_time = times[neurons == target][0]
            assert target_time >= source_time+delay
            assert min(stim.observation.event_time_us) > 0
        else:
            np.testing.assert_array_equal(stim.observation.counts, sham.observation.counts)
            assert stim.observation.event_time_us == sham.observation.event_time_us
        assert stim.receipt.delivered_start_us == 0
        assert stim.observation.available_us == 20000


def test_pending_delay_snapshot_and_synaptic_arrival():
    engine, source, target, channel, delay = responsive_fixture()
    monitor = b.StateMonitor(engine.group, ['I_E','v'], record=[target],
        when='end', clock=engine.clock, codeobj_class=NumpyCodeObject)
    engine.net.add(monitor)
    engine.group.namespace['stim_table'] = b.TimedArray(
        np.array([[0.,30.,30.,30.,30.]])*b.pA, dt=.02*b.second)
    engine.group.namespace['innovation'] = b.TimedArray(np.zeros((1,1000)), dt=.0001*b.second)
    # Check the real engine pathways with an event pending at the split.
    engine.net.run(1*b.ms, namespace={})
    source_times = np.rint(np.asarray(engine.monitor.t/b.us)).astype(int)[np.asarray(engine.monitor.i)==source]
    assert len(source_times) == 1 and source_times[0]+delay >= 1000
    engine.net.store('pending')
    engine.net.run(4*b.ms, namespace={})
    state = np.asarray(engine.group.v).copy()
    currents = np.asarray(monitor.I_E/b.pA).copy()
    times = np.rint(np.asarray(monitor.t/b.us)).astype(int)
    assert times[np.flatnonzero(currents[0] > 0)[0]] == source_times[0]+delay
    engine.net.restore('pending')
    engine.net.run(2*b.ms, namespace={}); engine.net.run(2*b.ms, namespace={})
    np.testing.assert_array_equal(state, np.asarray(engine.group.v))
    np.testing.assert_array_equal(currents, np.asarray(monitor.I_E/b.pA))


def test_membrane_decay_synaptic_signs_and_refractory():
    engine = BrianEngine(Config(retain_spikes=True))
    engine.group.namespace['background'] = 0*b.pA
    engine.group.namespace['noise_sigma'] = 0*b.pA
    engine.group.v = -60*b.mV
    engine.group.tau_m = 20*b.ms
    for syn in engine.synapses:
        syn.weight = 0*b.pA
    engine.advance(commands(engine, [(0.,)*4])[0], 20000)
    np.testing.assert_allclose(np.asarray(engine.group.v/b.mV), -65+5*math.exp(-1), atol=1e-10)
    engine.group.v = -60*b.mV
    engine.group.I_E = 0*b.pA; engine.group.I_I = 0*b.pA
    engine.group.I_E[0] = 20*b.pA; engine.group.I_I[1] = -20*b.pA
    engine.advance(commands(engine, [(0.,)*4])[0], 40000)
    assert engine.group.v[0] > engine.group.v[2] > engine.group.v[1]
    np.testing.assert_allclose(engine.group.I_E[0]/b.pA, 20*math.exp(-4), rtol=1e-12)
    np.testing.assert_allclose(engine.group.I_I[1]/b.pA, -20*math.exp(-2), rtol=1e-12)
    engine.group.namespace['background'] = 1000*b.pA
    trace = b.StateMonitor(engine.group, 'v', record=[0], clock=engine.clock,
                           when='end', codeobj_class=NumpyCodeObject)
    engine.net.add(trace)
    engine.advance(commands(engine, [(0.,)*4])[0], 60000)
    spike_us = np.rint(np.asarray(engine.monitor.t/b.us)).astype(int)[np.asarray(engine.monitor.i)==0]
    assert len(spike_us) > 1 and np.all(np.diff(spike_us) >= 2000)
    times = np.rint(np.asarray(trace.t/b.us)).astype(int)
    first = spike_us[0]
    np.testing.assert_array_equal(np.asarray(trace.v/b.mV)[0,(times>=first)&(times<first+2000)], -65.)


@pytest.mark.parametrize('change', [
    {'current_pA':(-1.,0.,0.,0.)}, {'current_pA':(math.nan,0.,0.,0.)},
    {'current_pA':(math.inf,0.,0.,0.)}, {'current_pA':(121.,0.,0.,0.)},
    {'current_pA':(31.,0.,0.,0.)}, {'current_pA':(1.,2.,3.)},
    {'current_pA':('30',0.,0.,0.)}, {'start_us':-20000},
    {'start_us':1}, {'start_us':False}, {'duration_us':100},
    {'trial_id':'other'}, {'command_id':''}, {'channels':(0,1,2,4)},
    {'schema_version':2}])
def test_invalid_actions_atomic(change):
    engine = BrianEngine(Config())
    initial = np.asarray(engine.group.v).copy()
    command = replace(Command('trial','a',0,(0.,)*4), **change)
    with pytest.raises(ValueError):
        engine.advance(command,20000)
    assert engine.time_us == 0 and float(engine.net.t/b.us) == 0
    np.testing.assert_array_equal(initial, np.asarray(engine.group.v))
    assert not engine.command_ids and not engine.noise_hashes


def test_total_slew_duplicate_and_missing_commands():
    engine = BrianEngine(Config())
    engine.run_commands(commands(engine, [(30.,)*4,(60.,)*4]))
    state = np.asarray(engine.group.v).copy()
    for current in [(90.,)*4,(120.,0.,0.,0.)]:
        with pytest.raises(ValueError):
            engine.advance(Command('trial','x',40000,current),60000)
    with pytest.raises(ValueError):
        engine.advance(Command('trial','c0',40000,(60.,)*4),60000)
    np.testing.assert_array_equal(state,np.asarray(engine.group.v))
    result = engine.advance(None,60000)
    assert result.receipt.delivered_current_pA == (30.,)*4
    assert result.receipt.requested_current_pA is None and result.receipt.status=='fallback'
    assert engine.advance(None,80000).receipt.delivered_current_pA == (0.,)*4
    with pytest.raises(ValueError): engine.advance(None,80000)


def test_half_open_channels_masks_and_filter():
    counts,rates,coverage,times,channels = bin_events(
        [0,19900,20000,0], [0,0,0,19],0,20000,np.ones(20,dtype=bool))
    assert counts[0] == 2 and counts[19] == 1 and counts.sum() == 3
    assert rates[0] == 20 and rates[1] == 0 and coverage[1] == 20000
    assert list(times)==[0,0,19900] and list(channels)==[0,19,0]
    mask=np.ones(20,dtype=bool);mask[0]=False
    counts,rates,coverage,*_ = bin_events([0],[0],0,20000,mask)
    assert counts[0]==-1 and np.isnan(rates[0]) and coverage[0]==0
    assert counts[1]==0 and rates[1]==0
    filter = RateFilter()
    base=np.zeros(20,dtype=int);base.reshape(4,5)[:,:4]=1
    for stop in range(7_020_000,15_000_001,20000):filter.update(base,stop)
    np.testing.assert_array_equal(filter.value, [10.]*4)
    _,filtered=filter.update(np.zeros(20,dtype=int),15_020_000)
    np.testing.assert_allclose(filtered, np.full(4,10*math.exp(-.2)),rtol=1e-14)
    # A shifted edge must be detectably different, rather than silently accepted.
    good=bin_events([19900],[0],0,20000,np.ones(20,dtype=bool))[0]
    shifted=bin_events([20000],[0],0,20000,np.ones(20,dtype=bool))[0]
    assert not np.array_equal(good,shifted)


def test_actual_ou_order_no_spike_dependent_stream_and_retention():
    engine=BrianEngine(Config())
    first_noise,_=innovations(Config(),0)
    engine.advance(commands(engine,[(0.,)*4])[0],20000)
    eta=np.zeros(1000);a=math.exp(-.1/5);scale=40*math.sqrt(1-a*a)
    for row in first_noise[:200]:eta=a*eta+scale*row
    np.testing.assert_allclose(engine.group.eta/b.pA,eta,rtol=1e-13,atol=1e-13)
    other=BrianEngine(Config(retain_spikes=True))
    other.advance(commands(other,[(30.,)*4])[0],20000)
    np.testing.assert_array_equal(engine.group.eta[:],other.group.eta[:])
    assert engine.noise_hashes==other.noise_hashes
    assert len(engine.monitor.i)==0 and len(other.monitor.i)>0


def test_process_isolation_public_firewall_and_reset():
    with Trial(Config(trial_id='a')) as a, Trial(Config(trial_id='b')) as c:
        ar=a.advance(Command('a','0',0,(30.,)*4),20000)
        assert c.time_us==0
        cr=c.advance(Command('b','0',0,(30.,)*4),20000)
        assert ar.observation.counts==cr.observation.counts
        assert ar.observation.event_time_us==cr.observation.event_time_us
        assert not hasattr(a,'group') and not hasattr(a,'net') and not hasattr(a,'gain')
        public=asdict(ar)
        assert not ({'v','eta','gain','weights','neurons','neuron_id'} & set(public))
        assert set(ar.observation.channel_id)<=set(range(20))
        assert all(0<=t<20000 for t in ar.observation.event_time_us)
        with pytest.raises(ValueError):a.advance(Command('a','bad',20000,(120.,)*4),40000)
        assert a.time_us==20000
        a.reset()
        replay=a.advance(Command('a','0',0,(30.,)*4),20000)
        observations_equal([ar],[replay])
        assert c.time_us==20000
    a.close()
    with pytest.raises(RuntimeError):a.advance(None,40000)


def test_zero_coupling_default_network_and_actual_channel_counts():
    engine=BrianEngine(Config(efficacy=0,retain_spikes=True))
    sequence=commands(engine,[(30.,)*4,(60.,)*4]+[(60.,)*4]*8)
    stimulated=engine.run_commands(sequence)
    all_t=np.rint(np.asarray(engine.monitor.t/b.us)).astype(np.int64)
    all_i=np.asarray(engine.monitor.i).copy()
    voltage=np.asarray(engine.group.v).copy()
    for result in stimulated:
        obs=result.observation
        selected=(all_t>=obs.start_us)&(all_t<obs.stop_us)
        for channel,members in enumerate(engine.parameters['recording']):
            expected=np.sum(selected & np.isin(all_i,members))
            assert obs.counts[channel]==expected
        assert sum(obs.counts)==len(obs.event_time_us)
    assert len(all_i)>sum(sum(r.observation.counts) for r in stimulated)
    engine.reset()
    sham=engine.run_commands(commands(engine,[(0.,)*4]*10))
    for stim,zero in zip(stimulated,sham):
        assert stim.observation.counts==zero.observation.counts
        assert stim.observation.event_time_us==zero.observation.event_time_us
    np.testing.assert_array_equal(voltage,np.asarray(engine.group.v))
    np.testing.assert_array_equal(all_t,np.rint(np.asarray(engine.monitor.t/b.us)))
    np.testing.assert_array_equal(all_i,np.asarray(engine.monitor.i))


def test_ou_precedes_membrane_update_on_first_sample():
    engine=BrianEngine(Config())
    noise,_=innovations(Config(),0)
    engine.group.namespace['innovation']=b.TimedArray(noise,dt=.0001*b.second)
    start=engine.parameters['initial_mV']
    tau=engine.parameters['tau_ms']
    eta=40*math.sqrt(1-math.exp(-2*.1/5))*noise[0]
    # pA / pF = V/s; times are in ms, giving mV directly here.
    equilibrium=-65 + (180+eta)*tau/200
    expected=equilibrium+(start-equilibrium)*np.exp(-.1/tau)
    engine.net.run(.1*b.ms,namespace={})
    expected=np.where(expected>=-50,-65,expected)
    np.testing.assert_allclose(engine.group.eta/b.pA,eta,rtol=1e-14,atol=1e-13)
    np.testing.assert_allclose(engine.group.v/b.mV,expected,rtol=1e-14,atol=1e-11)


@pytest.mark.parametrize('change',[
    {'network_id':-1},{'replicate_id':True},{'root_seed':1.5},
    {'dt_us':200},{'efficacy':math.nan},{'efficacy':-1},{'trial_id':''},
    {'retain_spikes':'yes'}])
def test_config_validation(change):
    with pytest.raises(ValueError):Config(**change)


def test_future_commands_cannot_mutate_previous_observations():
    engine=BrianEngine(Config())
    first=engine.advance(Command('trial','first',0,(0.,)*4),20000)
    frozen=asdict(first.observation)
    engine.advance(Command('trial','later',20000,(30.,)*4),40000)
    assert asdict(first.observation)['counts']==frozen['counts']
    assert asdict(first.observation)['event_time_us']==frozen['event_time_us']
    engine.reset()
    replay=engine.advance(Command('trial','first',0,(0.,)*4),20000)
    observations_equal([first],[replay])
