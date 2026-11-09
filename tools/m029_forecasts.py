"""Finite fixture forecasts, covariance paths and planner certificates."""
import runpy

import numpy as np

from tools.m027_residual_bounds import check_fixed_objective
from tools.m029_fits import Ball, endpoints, exact, fixed_inputs, join, maximum, members, require, ridge, state_pair
from tools.portable_numeric_verification import certify_choice


def state_ball(fit, model):
    result = fit.state(model.theta, model.p)
    return Ball(model.theta, result['coefficient_radius']), Ball(model.p, result['covariance_radius'])


def prediction(record, z, coefficient):
    result = Ball(record['output_mean']).add(Ball(z).product(coefficient))
    require(maximum(result) <= 100, 'FIR forecast guard crossed')
    return result


def propagate(fit, record, model, z, rate):
    _, covariance = state_ball(fit, model)
    zcol = Ball(z).reshape((len(z), 1))
    denominator = fit.forgetting.add(zcol.transpose.product(covariance).product(zcol))
    require(endpoints(denominator)[0].item() > 0, 'FIR denominator lower bound is nonpositive')
    fit.update(z, rate-np.asarray(record['output_mean']))


def fir_models(fixture, old, new, records, new_records, deadline):
    from neuromancer.predictive import FIRModel

    initial, z, target, inputs, rates = fixture
    row = initial.record
    theta = np.asarray(row['coef'])
    p = initial.information_inverse
    rows = []
    for kind in ('FIXED', 'RLS', 'BIAS'):
        fit = ridge(z, target)
        model = FIRModel(row, p, kind)
        coefficient, covariance, _, _ = state_pair(fit, theta, p, old['initial_theta'],
                                                   old['initial_information_inverse'])
        bias_p = Ball(model.bias_p)
        largest = 0.
        for i in range(100):
            deadline.check()
            k = 2400+i
            history = np.concatenate([inputs[k-lag] for lag in range(10)])
            x = model.standardized(history)
            estimate = prediction(row, x, coefficient)
            members(estimate, f'{kind} prediction {i}', old[kind+'_predictions'][i],
                    new[kind+'_predictions'][i], model.predict(history))
            largest = max(largest, float(estimate.radius.max()))
            if kind == 'RLS':
                propagate(fit, row, model, x, rates[k])
            elif kind == 'BIAS':
                error = Ball(rates[k]).subtract(Ball(row['output_mean'])).subtract(Ball(x).product(coefficient))
                gain = bias_p.divide_positive(Ball(.999).add(bias_p))
                bias_p = gain
                update = coefficient.part(0).add(gain.multiply(error))
                coefficient = join([update.reshape((1, 4)), coefficient.part(slice(1, None))])
            model.update(history, rates[k])
            require(model.failure is None, f'{kind} model failure')
            if kind == 'RLS':
                coefficient, covariance = state_ball(fit, model)
            members(coefficient, f'{kind} coefficient update {i}', model.theta)
            members(covariance, f'{kind} covariance update {i}', model.p)
        if kind == 'RLS':
            coefficient, covariance, _, _ = state_pair(fit, model.theta, model.p, old[kind+'_theta'], old[kind+'_p'])
        members(coefficient, f'{kind} final coefficients', old[kind+'_theta'], new[kind+'_theta'])
        members(covariance, f'{kind} final covariance', old[kind+'_p'], new[kind+'_p'])
        require(records[kind][:-1] == new_records[kind][:-1], f'{kind} discrete counts differ')
        members(bias_p, f'{kind} bias inverse', records[kind][-1], new_records[kind][-1])
        rows.append(dict(model=kind, forecasts=100, radius=largest))
    return rows


def online_models(old, new, records, new_records, deadline):
    from neuromancer import online_identify as online

    u, y, record, z, target, p = runpy.run_path('tests/test_online_identify.py')['fixture']()
    fixed_inputs('online', z, target, u, y)
    rows = []
    for kind in ('FROZEN', 'SHUFFLED', 'SW250', 'SW500', 'RLS995', 'RLS999'):
        fit = ridge(z, target)
        model = online.OnlineFIR(record, z, target, p, kind)
        coefficient, initial_covariance, _, _ = state_pair(fit, model.theta, p,
            old['FROZEN_online_theta'], old['FROZEN_online_p'])
        covariance = initial_covariance
        adaptive = kind.startswith('RLS')
        if adaptive:
            fit.forgetting = Ball(.995 if kind == 'RLS995' else .999)
        largest = 0.
        for i in range(50):
            deadline.check()
            k = 1950+i
            x = online.features(u, np.array([k]))[0]
            standardized = online.standardized(record, x[None])[0]
            estimate = prediction(record, standardized, coefficient).reshape((1, 4))
            members(estimate, f'{kind} forecast {i}', old[kind+'_online_forecasts'][i],
                    new[kind+'_online_forecasts'][i], model.forecast(x[None], model.time_us))
            largest = max(largest, float(estimate.radius.max()))
            if adaptive:
                propagate(fit, record, model, standardized, y[k])
            model.update(x, y[k], model.time_us+20000, model.time_us+20000)
            require(not model.failed, f'{kind} online update failed')
            if adaptive:
                coefficient, covariance = state_ball(fit, model)
        if kind.startswith('SW'):
            width = int(kind[2:])
            window = ridge(np.asarray(model.z[-width:]), np.asarray(model.target[-width:]))
            inverse = np.linalg.inv(window.information.center)
            coefficient, _, _, _ = state_pair(window, model.theta, inverse, old[kind+'_online_theta'], inverse)
        elif adaptive:
            coefficient, covariance, _, _ = state_pair(fit, model.theta, model.p,
                old[kind+'_online_theta'], old[kind+'_online_p'])
        members(coefficient, f'{kind} online coefficients', old[kind+'_online_theta'], new[kind+'_online_theta'])
        members(covariance, f'{kind} online covariance', old[kind+'_online_p'], new[kind+'_online_p'])
        require(records[kind+'_online'] == new_records[kind+'_online'], f'{kind} causal state differs')
        rows.append(dict(model=kind, forecasts=50, radius=largest))
    return rows


def planner_fixtures(fixture, old, new, records, new_records, deadline):
    from neuromancer.predictive_planner import GRID, plan

    initial, z, target, *_ = fixture
    record = initial.record
    fit = ridge(z, target)
    theta = np.asarray(record['coef'])
    coefficient, _, _, _ = state_pair(fit, theta, initial.information_inverse,
                                       old['initial_theta'], old['initial_information_inverse'])
    b = coefficient.part(slice(1, None)).divide_positive(Ball(np.asarray(record['scale'])[:, None]))
    c = Ball(record['output_mean']).add(coefficient.part(0)).subtract(Ball(record['mean']).product(b))
    slopes = b.reshape((10, 4, 4))
    kernels = slopes.part((slice(None), 0)).add(slopes.part((slice(None), 2)))
    rows = []
    for previous in (0., 37.3, 60., np.nextafter(120., 0.), 120.):
        deadline.check()
        prefix = f'planner_{previous}_'
        history = np.zeros((9, 4))
        history[:, ::2] = previous
        native = plan(record, theta, history, 9., 51_000_000, clock=lambda: 0)
        bank = native['bank']
        for name in ('bank', 'first', 'dose', 'switch', 'exposure'):
            exact(old[prefix+name], native[name], prefix+name)
            exact(old[prefix+name], new[prefix+name], prefix+name)
        check_fixed_objective(native, {key: old[prefix+key] for key in ('dose', 'switch', 'exposure')})
        full = np.c_[np.broadcast_to(history[:, 0], (625, 9)), bank]
        pred = c
        for lag in range(10):
            pred = pred.add(Ball(full[:, 9-lag:109-lag, None]).multiply(kernels.part(lag)))
        require(maximum(pred) <= 100, 'Planner candidate forecast guard crossed')
        means = pred.reshape((625, 2, 50, 4)).mean((2, 3))
        error = means.subtract(Ball(9.))
        tracking = error.multiply(error).mean((1,)).multiply(Ball(2.))
        cost = tracking.add(Ball(native['dose'])).add(Ball(native['switch']))
        for name, interval in [('predictions', pred), ('tracking', tracking), ('cost', cost)]:
            members(interval, prefix+name, old[prefix+name], new[prefix+name], native[name])
        chosen = native['chosen']
        for name in ('chosen', 'q0', 'q1', 'origin_us'):
            require(records[prefix+name] == new_records[prefix+name] == native[name],
                    f'Planner record changed: {prefix}{name}')
        for arrays, meta in [(old, records), (new, new_records)]:
            exact(meta[prefix+'minimum_forecast'], float(arrays[prefix+'predictions'].min()), prefix+'minimum')
        certify_choice(cost, chosen, np.repeat(GRID, len(GRID)), np.tile(GRID, len(GRID)), bank)
        lower, upper = endpoints(cost)
        gap = np.delete(lower, chosen).min() - upper[chosen]
        rows.append(dict(previous=float(previous), candidates=625, chosen=chosen,
                         prediction_radius=float(pred.radius.max()), cost_radius=float(cost.radius.max()),
                         certified_nonchosen_cost_gap_lower=float(np.nextafter(gap, -np.inf))))
    return rows


def controller_and_feedback(fixture, old, new, records, new_records, deadline):
    from neuromancer.predictive import FIRModel, PredictiveController

    initial, z, target, *_ = fixture
    tools = runpy.run_path('tests/test_predictive.py')
    rows = []
    for kind in ('FIXED', 'RLS'):
        fit = ridge(z, target)
        controller = PredictiveController(initial, kind, clock=lambda: 0)
        for i in range(250):
            deadline.check()
            command = controller.command(controller.time_us)
            exact(old[kind+'_actions'][i], command.current_pA, f'{kind} delivered action {i}')
            observation = None if i == 73 else tools['observation'](controller.time_us, 8.+i%5)
            model = controller.model
            # The frozen event ledger records eligibility after the original rearm rules.
            event = records[kind+'_events'][i]
            if kind == 'RLS' and event['valid_update']:
                x = model.standardized(controller.pending[1])
                rate = np.asarray(observation.counts).reshape(4, 5)[:, :4].sum(1)/.4
                propagate(fit, model.record, model, x, rate)
            controller.accept(observation, tools['receipt'](command), controller.time_us+20000)
            require(controller.events[-1] == event, f'{kind} event {i} changed')
            state_ball(fit, model)
        exact(old[kind+'_actions'], new[kind+'_actions'], f'{kind} all actions')
        coefficient, covariance, _, _ = state_pair(fit, model.theta, model.p,
            old[kind+'_controller_theta'], old[kind+'_controller_p'])
        members(coefficient, kind+' controller coefficients', new[kind+'_controller_theta'])
        members(covariance, kind+' controller covariance', new[kind+'_controller_p'])
        require(records[kind+'_events'] == new_records[kind+'_events'], f'{kind} event ledger changed')
        rows.append(dict(model=kind, updates=model.updates, decisions=250,
                         radius=float(coefficient.radius.max())))

    require(records['feedback'] == new_records['feedback'], 'Feedback receipts/counts differ')
    fit = ridge(z, target)
    model = FIRModel(initial.record, initial.information_inverse, 'RLS')
    history = np.zeros((10, 4))
    for i, row in enumerate(records['feedback']):
        deadline.check()
        history[-1] = row['receipt']['delivered_current_pA']
        x = history[::-1].ravel()
        standardized = model.standardized(x)
        coefficient, _ = state_ball(fit, model)
        estimate = prediction(model.record, standardized, coefficient)
        members(estimate, f'feedback forecast {i}', old['feedback_forecasts'][i], new['feedback_forecasts'][i])
        rate = np.asarray(row['counts']).reshape(4, 5)[:, :4].sum(1)/.4
        propagate(fit, model.record, model, standardized, rate)
        model.update(x, rate)
        require(model.failure is None, 'Feedback update failed')
        history[:-1] = history[1:]
    coefficient, _, _, _ = state_pair(fit, model.theta, model.p, old['feedback_coefficients'], model.p)
    members(coefficient, 'feedback coefficients', new['feedback_coefficients'])
    rows.append(dict(model='feedback', updates=model.updates, radius=float(coefficient.radius.max())))
    return rows


def graph_weights(expected, actual):
    from neuromancer._brian import E_COUNT, N, realization, stream
    from neuromancer.substrate import Config
    import brian2 as brian

    exact(expected[:, (0, 1, 3)], actual[:, (0, 1, 3)], 'graph indices and delays')
    config = Config()
    edges = realization(config)
    exc = edges['pre'] < E_COUNT
    uniform = np.empty(len(exc))
    rng = stream(config, 2)
    uniform[exc] = rng.random(int(exc.sum()))
    uniform[~exc] = rng.random(int((~exc).sum()))
    full_keys = edges['pre']*N + edges['post']
    keys = (expected[:, 0]*N + expected[:, 1]).astype(int)
    indices = np.searchsorted(full_keys, keys)
    exact(keys, full_keys[indices], 'graph random stream order')
    exact(expected[:, 3], edges['delay_us'][indices].astype(float), 'graph generated delays')
    # Both separate and fused affine paths are enclosed. The latter has only
    # the final addition's rounding, already included by Ball.add.
    weights = Ball(uniform[indices]).multiply(Ball(np.where(exc[indices], 6., 24.)))
    weights = weights.add(Ball(np.where(exc[indices], 12., -72.)))
    unit = Ball(float(brian.pA))
    weights = weights.multiply(unit).divide_positive(unit)
    members(weights, 'DAG affine and unit conversion', expected[:, 2], actual[:, 2])
    return dict(edges=len(expected), radius=float(weights.radius.max()))
