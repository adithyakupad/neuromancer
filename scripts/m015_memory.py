"""M015 bounded benchmark, access and conditional retention acquisition."""

from dataclasses import replace
import json
import os
from pathlib import Path
import resource
import sys
import time

import numpy as np
from scipy.stats import t
from neuromancer.causal_memory import audit_graph, build_condition, cue_gate, effective_edges
from neuromancer.functional_learning import balanced_accuracy
from neuromancer.reservoir import (
    commands_for_trial,
    features,
    representation_diagnostics,
    reset_trial,
    score_readout,
    symbols,
)
from neuromancer.substrate import Config
from neuromancer.supervisor import Deadline, atomic_json

NETWORKS = (15000, 15001)
CONDITIONS = ("C0", "C1", "C2")


def resource_usage(output):
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = peak if sys.platform == "darwin" else peak * 1024
    size = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    if rss > 2 * 1024**3 or size > 100 * 1024**2:
        raise RuntimeError("M015 measured resource limit exceeded")
    return dict(peak_rss_bytes=rss, artifact_bytes=size)


def run_trial(engine, condition, pair, delay, replicate, *, cue_only=False, sham=False):
    Deadline.from_environment().check()
    if Path(os.environ["NEUROMANCER_STOP_FILE"]).exists():
        raise RuntimeError("M015 cooperative stop")
    reset_trial(engine, replicate, condition != "C1")
    commands = commands_for_trial(*map(int, pair), delay, engine.config.trial_id)
    if cue_only:
        commands = commands[:4]
    if sham:
        commands = [replace(command, current_pA=(0.0, 0.0, 0.0, 0.0)) for command in commands]
    results = engine.run_commands(commands)
    counts = np.array([r.observation.counts for r in results])
    if not np.isfinite(counts).all() or counts.mean() / (5 * 0.02) > 100:
        raise RuntimeError("Recorded activity gate failed")
    cue = features(results[:4], 80000)[0]
    observations = {"cue": cue}
    if not cue_only:
        distractor_end = 8 + delay // 20
        observations["distractor"] = features(results[:distractor_end], distractor_end * 20000)[0]
        observations["final"] = features(results, len(results) * 20000)[0]
    raw = dict(
        counts=counts.tolist(),
        noise_id=replicate,
        noise_hashes=engine.noise_hashes,
        start_us=[r.receipt.delivered_start_us for r in results],
        available_us=[r.observation.available_us for r in results],
        delivered=[r.receipt.delivered_current_pA for r in results],
        requested=[command.current_pA for command in commands],
    )
    return observations, raw


def benchmark(output):
    began = time.perf_counter()
    engine = build_condition(Config(network_id=15000, root_seed=20261106), "C0")
    construction = time.perf_counter() - began
    samples = []
    for replicate in range(159000, 159003):
        started = time.perf_counter()
        run_trial(engine, "C0", (0, 1), 80, replicate)
        samples.append(time.perf_counter() - started)
    engine.close()
    forecasts = {
        stage: 2 * (6 * construction + count * max(samples)) + 30
        for stage, count in [("access", 336), ("retention", 720)]
    }
    atomic_json(
        output / "benchmark.json",
        dict(
            construction_s=construction,
            trial_s=samples,
            simulated_s=1.08,
            forecasts_s=forecasts,
            **resource_usage(output),
        ),
    )


def bank(engine, condition, output, *, access, delay, delay_index):
    network = engine.config.network_id
    prefix = f"{network}_{condition}_D{delay}"
    matrices, symbols_by_split, sham_features = {}, {}, []
    sham_null = True
    for split_index, (split, size) in enumerate([("fit", 16), ("validation", 8), ("test", 16)]):
        inputs = symbols(network, 0 if access else delay_index + 1, split_index, size)
        trials, raw_records = [], []
        for index, pair in enumerate(inputs):
            replicate = (
                (150000 if access else 151000 + 1000 * delay_index) + 100 * split_index + index
            )
            observed, raw = run_trial(engine, condition, pair, delay, replicate, cue_only=access)
            if access and split == "test":
                sham, sham_raw = run_trial(
                    engine, condition, pair, delay, replicate, cue_only=True, sham=True
                )
                raw["sham"] = sham_raw
                sham_features.append(sham["cue"])
                sham_null &= raw["counts"] == sham_raw["counts"]
            trials.append(observed)
            raw_records.append(raw)
        matrices[split] = {name: np.array([trial[name] for trial in trials]) for name in trials[0]}
        symbols_by_split[split] = inputs
        atomic_json(
            output / f"{prefix}_{split}_raw.json", dict(symbols=inputs.tolist(), trials=raw_records)
        )
        resource_usage(output)
    results = {}
    labels = {name: values[:, 0] for name, values in symbols_by_split.items()}
    for window in matrices["fit"]:
        fit, validation, test = (matrices[split][window] for split in ("fit", "validation", "test"))
        fitted, predictions = score_readout(
            fit, validation, test, labels["fit"], labels["validation"]
        )
        np.savez_compressed(
            output / f"{prefix}_{window}.npz",
            fit=fit,
            validation=validation,
            test=test,
            mean=fitted[0],
            scale=fitted[1],
            coefficients=fitted[2],
            predictions=predictions,
            labels=labels["test"],
        )
        rates = test.reshape(-1, 4, 5)
        result = dict(
            accuracy=balanced_accuracy(labels["test"], predictions),
            rate_hz=float(test.mean()),
            e_hz=float(rates[:, :, :4].mean()),
            i_hz=float(rates[:, :, 4].mean()),
            alpha_index=fitted[3],
            validation_scores=fitted[4],
            representation=representation_diagnostics(fit),
        )
        if access:
            contrast = test - np.array(sham_features)
            result.update(
                exact_sham_null=bool(sham_null),
                evoked_rms_hz=[
                    float(np.sqrt(np.mean(contrast[labels["test"] == label].mean(axis=0) ** 2)))
                    for label in (0, 1)
                ],
            )
        else:
            result["by_distractor"] = [
                balanced_accuracy(labels["test"][mask], predictions[mask])
                for mask in (
                    symbols_by_split["test"][:, 1] == 0,
                    symbols_by_split["test"][:, 1] == 1,
                )
            ]
        results[window] = result
    return results


def acquire(output, access):
    started = time.perf_counter()
    all_networks = {}
    for network in NETWORKS:
        conditions = {}
        for condition in CONDITIONS:
            engine = build_condition(
                Config(
                    network_id=network, root_seed=20261106, trial_id=f"m015-{network}-{condition}"
                ),
                condition,
            )
            try:
                graph = audit_graph(engine)
                if condition == "C2" and (
                    graph["largest_scc"] != 1
                    or graph["self_edges"]
                    or any(hops is None for channel in graph["recorder_hops"] for hops in channel)
                ):
                    raise RuntimeError("DAG connectivity gate failed")
                np.savez_compressed(
                    output / f"{network}_{condition}_graph.npz",
                    edges=effective_edges(engine),
                    stimulation=engine.parameters["stimulation"],
                    recording=engine.parameters["recording"],
                )
                atomic_json(
                    output / f"{network}_{condition}_graph.json",
                    dict(graph=graph, parameters=engine.public_metadata()["parameter_hashes"]),
                )
                delays = [80] if access else [20, 80, 160]
                conditions[condition] = {
                    str(delay): bank(
                        engine, condition, output, access=access, delay=delay, delay_index=index
                    )
                    for index, delay in enumerate(delays)
                }
                atomic_json(output / f"{network}_{condition}_metrics.json", conditions[condition])
            finally:
                engine.close()
        all_networks[str(network)] = conditions
    summary = dict(
        networks=all_networks,
        elapsed_s=time.perf_counter() - started,
        simulated_s=26.88 if access else 268.8,
        **resource_usage(output),
    )
    if access:
        gates = {
            network: cue_gate(
                {condition: cells["80"]["cue"] for condition, cells in conditions.items()}
            )
            for network, conditions in all_networks.items()
        }
        summary["gate"] = "PASS" if all(all(gate.values()) for gate in gates.values()) else "HOLD"
        summary["criteria"] = gates
    else:
        effects = np.array(
            [
                100
                * (data["C0"]["80"]["final"]["accuracy"] - data["C2"]["80"]["final"]["accuracy"])
                for data in all_networks.values()
            ]
        )
        margin = float(t.ppf(0.975, 1) * effects.std(ddof=1) / np.sqrt(2))
        summary.update(
            effect_pp=float(effects.mean()),
            network_effects_pp=effects.tolist(),
            ci95_pp=[float(effects.mean() - margin), float(effects.mean() + margin)],
        )
    atomic_json(output / "summary.json", summary)


if __name__ == "__main__":
    stage, destination = sys.argv[1:3]
    output = Path(destination)
    if stage == "benchmark":
        benchmark(output)
    else:
        if stage not in ("access", "retention"):
            raise ValueError("Invalid stage")
        evidence = json.loads(Path(sys.argv[3]).read_text())
        if evidence["forecasts_s"][stage] > (420 if stage == "access" else 1100):
            raise RuntimeError("M015 forecast gate HOLD")
        if stage == "retention" and json.loads(Path(sys.argv[4]).read_text())["gate"] != "PASS":
            raise RuntimeError("M015 cue-access HOLD")
        acquire(output, stage == "access")
