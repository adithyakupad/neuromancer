import numpy as np
import pytest
from neuromancer.state_dependence import origin_rate, thresholds, label, inputs, matrix, solve, effect, gate, arx_matrix, arx_forecast
from neuromancer.state_experiment import plans, arrays
from neuromancer.identification_experiment import audit
from neuromancer.substrate import Config


def test_state_causal_and_history_mutations():
    y = np.arange(400, dtype=float).reshape(100, 4)/100
    a = origin_rate(y)
    y[:-5] = -999
    assert origin_rate(y) == a
    assert origin_rate(y[-5:]) == a
    with pytest.raises(ValueError): origin_rate(y[-4:])
    calibration = np.tile(np.arange(500)[:, None], (1, 4))
    b = thresholds(calibration)
    assert b == pytest.approx(np.quantile(np.arange(2, 498), [.25, .75]))
    assert label(np.ones((5, 4))*b[0], b) == 'LOW'
    assert label(np.ones((5, 4))*b[1], b) == 'HIGH'
    with pytest.raises(ValueError): thresholds(np.ones((500, 4)))


def test_interaction_analytical_recovery_and_zero():
    rng = np.random.default_rng(61)
    xs = []; ys = []
    for a in (-2., 2.):
        u = rng.uniform(0, 10, (150, 4)); x = matrix(u, a, 0., 1., 'STATE')
        beta = np.zeros((80, 4)); beta[:4] = np.eye(4)*.03; beta[40:44] = np.eye(4)*.01
        xs.append(x); ys.append(x@beta)
    x = np.vstack(xs); y = np.vstack(ys); record = solve(x, y, .0001)
    record.update(family='STATE', state_mean=0., state_sd=1.)
    assert np.mean((effect(record, u, 2.)-ys[-1])**2) < 1e-5
    np.testing.assert_array_equal(effect(record, np.zeros((100, 4)), 50.), np.zeros((100, 4)))
    assert np.max(np.abs(effect(record, u, -2.)-effect(record, u, 2.))) > .1
    z = x/np.array(record['scale']); reference = np.linalg.solve(z.T@z+len(z)*.0001*np.eye(80), z.T@y)
    np.testing.assert_allclose(record['coef'], reference, atol=1e-11)


def test_fir_future_mutation_and_no_state_access():
    rng = np.random.default_rng(62); u = rng.uniform(0, 10, (100, 4)); x = inputs(u)
    b = rng.normal(0, .001, (40, 4)); record = solve(x, x@b, .001)
    record.update(family='FIR', state_mean=0., state_sd=.1)
    before = effect(record, u)
    mutated = u.copy(); mutated[40:] = 70
    np.testing.assert_array_equal(effect(record, mutated)[:40], before[:40])
    np.testing.assert_array_equal(effect(record, u, object()), before)
    np.testing.assert_array_equal(x[0, 4:], np.zeros(36))


def test_exact_schedule_exposure_and_constraints():
    for n in range(10):
        for rep in range(26, 32):
            desired, planned = plans(Config(network_id=n, replicate_id=rep))
            assert planned.shape == (7, 100, 4)
            for row in planned: assert audit(row)['violations'] == 0
            assert not planned[0].any()
            # Both strata receive this same plan; all single channels represented.
            assert len(set(np.argmax(desired[j].sum(axis=0)) for j in range(1, 5))) == 4


def test_network_gate_and_no_pseudoreplication():
    f = np.ones(10); s = np.full(10, .8); sh = np.full(10, .9)
    g = gate(f, s, sh)
    assert g['decision'] == 'PASS' and g['positive_networks'] == 10
    assert gate(f, f, sh)['decision'] == 'FAIL'
    with pytest.raises(ValueError): gate(np.ones(100), np.zeros(100), np.ones(100))


def test_arx_timestamp_and_recursive_alignment():
    h = np.arange(200).reshape(50, 4)/100; y = np.zeros((100, 4)); u = np.zeros((100, 4)); u[0] = 1
    x = arx_matrix(h, y, u)
    np.testing.assert_array_equal(x[0, :4], h[-1])
    np.testing.assert_array_equal(x[0, 16:20], u[0])
    coef = np.zeros((33, 4)); coef[1:5] = np.eye(4)*.5; coef[17:21] = np.eye(4)*.1
    rec = dict(coef=coef, mean=np.zeros(32), scale=np.ones(32), output_mean=np.zeros(4), intercept=True)
    pred = arx_forecast(rec, h, u)
    np.testing.assert_allclose(pred[0], .5*h[-1]+.1)
    np.testing.assert_allclose(pred[1], .5*pred[0])


def test_origin_checkpoint_replay_and_receipt_timing():
    from neuromancer._brian import BrianEngine
    from neuromancer.diagnostic import schedule
    from neuromancer.reachability import state_hashes
    engine = BrianEngine(Config(trial_id='state-fixture'))
    try:
        engine.run_commands(schedule(engine, np.zeros((5, 4))))
        engine.save('origin'); checkpoint = state_hashes(engine)
        p = np.zeros((10, 4)); p[:5, 0] = 30
        first = arrays(engine.run_commands(schedule(engine, p)))
        engine.restore('origin'); assert state_hashes(engine) == checkpoint
        second = arrays(engine.run_commands(schedule(engine, p)))
        for key in first: np.testing.assert_equal(first[key], second[key])
        assert first['time_us'][0].tolist() == [100000, 120000, 120000]
        assert not set(engine.parameters['recording'].ravel()) & set(engine.parameters['stimulation'].ravel())
    finally: engine.close()
