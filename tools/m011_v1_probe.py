"""Readability-only golden outputs and bounded engineering timings; no study data."""
import argparse
import hashlib
import json
import platform
import resource
import runpy
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from neuromancer import Command, Config
from neuromancer import identify, online_identify
from neuromancer._brian import BrianEngine
from neuromancer.control import Policy, project
from neuromancer.predictive import FIRModel, PredictiveController
from neuromancer.predictive_planner import plan


def zero_clock():
    # Only golden controller outputs use this deterministic injected clock.
    # Production native-clock deadline behavior is exercised by regression tests.
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--neural", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    tests = runpy.run_path("tests/test_predictive.py")
    initial, design, targets, inputs, rates = tests["fixture"]()
    observation = tests["observation"]
    receipt = tests["receipt"]
    arrays = {}
    records = {}
    timings = {}

    def retain(name, value):
        arrays[name] = np.asarray(value)

    def measure(name, function, repeats=9):
        # Warm-up remains recorded; no outlier removal or best-run selection.
        wall = []
        cpu = []
        for _ in range(repeats):
            start = time.perf_counter_ns()
            start_cpu = time.process_time_ns()
            function()
            cpu.append(time.process_time_ns() - start_cpu)
            wall.append(time.perf_counter_ns() - start)
        timings[name] = {"wall_ns": wall, "cpu_ns": cpu}

    retain("initial_design", design)
    retain("initial_targets", targets)
    retain("initial_theta", initial.record["coef"])
    retain("initial_information_inverse", initial.information_inverse)
    records["initial"] = initial.record
    for kind in ("FIXED", "RLS", "BIAS"):
        model = FIRModel(initial.record, initial.information_inverse, kind)
        predictions = []
        for index in range(100):
            k = 2400 + index
            history = np.concatenate([inputs[k - lag] for lag in range(10)])
            predictions.append(model.predict(history))
            model.update(history, rates[k])
        retain(kind + "_predictions", predictions)
        retain(kind + "_theta", model.theta)
        retain(kind + "_p", model.p)
        records[kind] = [model.received, model.updates, model.skips, model.failure, model.bias_p]

    online_tests = runpy.run_path("tests/test_online_identify.py")
    u, y, record, z, target, p = online_tests["fixture"]()
    for kind in ("FROZEN", "SHUFFLED", "SW250", "SW500", "RLS995", "RLS999"):
        model = online_identify.OnlineFIR(record, z, target, p, kind)
        forecasts = []
        for index in range(50):
            x = online_identify.features(u, np.array([1950 + index]))[0]
            forecasts.append(model.forecast(x[None], model.time_us))
            stop = model.time_us + 20000
            model.update(x, y[1950 + index], stop, stop)
        retain(kind + "_online_forecasts", forecasts)
        retain(kind + "_online_theta", model.theta)
        retain(kind + "_online_p", model.p)
        records[kind + "_online"] = [model.updates, model.skips, model.refits, model.failed, model.failures]

    rng = np.random.default_rng(20261104)
    u = rng.uniform(0, 30, (3300, 4))
    y = np.full((3300, 4), 8.0)
    for index in range(1, len(y)):
        y[index] = 8 + .4 * (y[index - 1] - 8) + .002 * u[index] + rng.normal(0, .02, 4)
    for family in identify.FAMILIES:
        for lag_count in (1, 4):
            model = identify.fit(y, u, family, lag_count)
            name = family + str(lag_count)
            records[name] = model.record()
            retain(name + "_prediction", model.forecast(y[:3200], u[:3200], u[3200:3250]))
    records["bootstrap"] = identify.bootstrap(np.arange(40).reshape(10, 4) / 10)
    records["qualification"] = identify.qualification(np.tile([2., 1., .8, 1.1], (10, 1)))

    for previous in (0., 37.3, 60., np.nextafter(120., 0.), 120.):
        history = np.zeros((9, 4))
        history[:, ::2] = previous
        result = plan(initial.record, initial.record["coef"], history, 9., 51_000_000, clock=zero_clock)
        for name, value in result.items():
            if isinstance(value, np.ndarray):
                retain(f"planner_{previous}_{name}", value)
            elif name != "elapsed_ns":
                records[f"planner_{previous}_{name}"] = value

    for kind in ("FIXED", "RLS"):
        controller = PredictiveController(initial, kind, clock=zero_clock)
        actions = []
        for index in range(250):
            command = controller.command(controller.time_us)
            obs = None if index == 73 else observation(controller.time_us, 8. + index % 5)
            controller.accept(obs, receipt(command), controller.time_us + 20000)
            actions.append(command.current_pA)
        retain(kind + "_actions", actions)
        retain(kind + "_controller_theta", controller.model.theta)
        retain(kind + "_controller_p", controller.model.p)
        records[kind + "_events"] = controller.events

    policy = Policy(initial.calibration, "PI10_5")
    previous = np.zeros(4)
    state = []
    actions = []
    for index in range(2000):
        previous, status = project(policy.desired(), previous)
        actions.append(previous.copy())
        if index == 73:
            policy.missing(policy.expected_us + 20000)
        else:
            policy.accept(observation(policy.expected_us, float(6 + (index // 100) % 9)), policy.expected_us + 20000)
        state.append(policy.record())
    retain("pi_state", state)
    retain("pi_actions", actions)
    assert np.max(np.abs(np.diff(actions, axis=0))) <= 30
    assert np.max(np.sum(actions, axis=1)) <= 240

    x = np.concatenate([inputs[2400 - lag] for lag in range(10)])
    model = FIRModel(initial.record, initial.information_inverse, "RLS")
    measure("fir_1000_predictions", lambda: [model.predict(x) for _ in range(1000)])
    measure("rls_100_updates", lambda: [model.update(x, rates[2400]) for _ in range(100)])
    measure("planner_625_candidates", lambda: plan(initial.record, initial.record["coef"], initial.history, 9., 51_000_000, limit_s=10))

    def pi_decisions():
        policy = Policy(initial.calibration, "PI10_5")
        for _ in range(1000):
            policy.accept(observation(policy.expected_us), policy.expected_us + 20000)

    measure("pi_1000_observations", pi_decisions)
    measure("arx_fit", lambda: identify.fit(y, u, "ARX", 4))

    if args.neural:
        engine = BrianEngine(Config(retain_spikes=True))
        commands = [Command(engine.config.trial_id, f"style-{i}", i * 20000,
                    (min(120., 30. * (i + 1)), 0., min(120., 30. * (i + 1)), 0.)) for i in range(50)]
        results = engine.run_commands(commands)
        retain("neural_counts", [r.observation.counts for r in results])
        retain("neural_sector", [r.observation.sector_rate_hz for r in results])
        import brian2 as b
        retain("spike_i", engine.monitor.i[:])
        retain("spike_us", np.asarray(engine.monitor.t / b.us))
        engine.reset()
        replay = engine.run_commands(commands, chunked=True)
        np.testing.assert_array_equal(arrays["neural_counts"], [r.observation.counts for r in replay])
        np.testing.assert_array_equal(arrays["spike_i"], engine.monitor.i[:])
        np.testing.assert_array_equal(arrays["spike_us"], np.asarray(engine.monitor.t / b.us))
        records["config"] = asdict(engine.config)
        records["neural_replay"] = "exact continuous/chunked events and observations"

    np.savez_compressed(args.output / "outputs.npz", **arrays)
    (args.output / "records.json").write_text(json.dumps(records, sort_keys=True, indent=2, allow_nan=False))
    hashes = {name: hashlib.sha256(value.tobytes()).hexdigest() for name, value in arrays.items()}
    result = dict(array_count=len(arrays), array_hashes=hashes, timings=timings,
                  environment=dict(python=sys.version, platform=platform.platform(), numpy=np.__version__),
                  max_rss_native_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if args.reference:
        reference = np.load(args.reference / "outputs.npz")
        assert set(reference.files) == set(arrays)
        for name, value in arrays.items():
            expected = reference[name]
            assert expected.dtype == value.dtype and expected.shape == value.shape, name
            assert expected.tobytes() == value.tobytes(), name
        assert (args.reference / "records.json").read_bytes() == (args.output / "records.json").read_bytes()
        result["exact_equivalence"] = True
    (args.output / "measurements.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("timings", "array_hashes")}))


if __name__ == "__main__":
    main()
