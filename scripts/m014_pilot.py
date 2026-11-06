"""Frozen M014 pilot. No plasticity, hidden-state features or test-label tuning."""

import json
import os
from pathlib import Path
import resource
import sys
import time
import numpy as np
from neuromancer._brian import BrianEngine
from neuromancer.substrate import Config, Command
from neuromancer.supervisor import Deadline, atomic_json
from neuromancer.reservoir import (
    DELAYS_MS,
    SPLIT_SIZES,
    symbols,
    commands_for_trial,
    features,
    reset_trial,
    generator,
    score_readout,
    representation_diagnostics,
)
from neuromancer.functional_learning import balanced_accuracy


def save_prediction(output, prefix, name, fit_x, validation_x, test_x, fit_y, validation_y, truth):
    fitted, prediction = score_readout(fit_x, validation_x, test_x, fit_y, validation_y)
    np.savez_compressed(
        output / f"{prefix}_{name}.npz",
        fit=fit_x,
        validation=validation_x,
        test=test_x,
        fit_labels=fit_y,
        validation_labels=validation_y,
        test_labels=truth,
        predictions=prediction,
        mean=fitted[0],
        scale=fitted[1],
        coefficients=fitted[2],
    )
    return dict(
        model=name,
        accuracy=balanced_accuracy(truth, prediction),
        alpha_index=fitted[3],
        validation_scores=fitted[4],
        feature_count=fit_x.shape[1],
        parameter_count=fit_x.shape[1] + 1,
    )


def check_resources(output):
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    size = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    if peak_bytes > 2 * 1024**3 or size > 200 * 1024**2:
        raise RuntimeError("Declared memory/storage ceiling exceeded")
    return dict(peak_rss_bytes=peak_bytes, artifact_bytes=size)


def main(output):
    deadline = Deadline.from_environment()
    summary = []
    started = time.perf_counter()
    for network in [14000, 14001]:
        for condition in ["C0", "C1"]:
            deadline.check()
            build_start = time.perf_counter()
            engine = BrianEngine(
                Config(
                    network_id=network,
                    root_seed=20261105,
                    replicate_id=140000,
                    trial_id=f"m014-{network}-{condition}",
                )
            )
            build_s = time.perf_counter() - build_start
            try:
                for delay_index, delay in enumerate(DELAYS_MS):
                    split_features = {}
                    split_symbols = {}
                    prefix = f"{network}_{condition}_D{delay}"
                    activity = []
                    split_costs = {}
                    for split_index, (split, size) in enumerate(SPLIT_SIZES.items()):
                        split_start = time.perf_counter()
                        values = symbols(network, delay_index, split_index, size)
                        split_symbols[split] = values
                        collected = {
                            name: [] for name in ["final", "history", "cue_end", "distractor_end"]
                        }
                        trial_records = []
                        for trial, (cue, distractor) in enumerate(values):
                            deadline.check()
                            if Path(os.environ["NEUROMANCER_STOP_FILE"]).exists():
                                raise RuntimeError("Cooperative stop")
                            noise_id = 140000 + delay_index * 1000 + split_index * 100 + trial
                            reset_trial(engine, noise_id, condition == "C0")
                            commands = commands_for_trial(
                                int(cue), int(distractor), delay, engine.config.trial_id
                            )
                            result = engine.run_commands(commands)
                            final, history = features(result, len(commands) * 20000)
                            cue_end, _ = features(result[:4], 80000)
                            second_end = 8 + delay // 20
                            distractor_end, _ = features(result[:second_end], second_end * 20000)
                            collected["final"].append(final)
                            collected["history"].append(history)
                            collected["cue_end"].append(cue_end)
                            collected["distractor_end"].append(distractor_end)
                            counts = np.array([step.observation.counts for step in result])
                            rates = counts / (5 * 0.02)
                            activity.append(rates)
                            trial_records.append(
                                dict(
                                    noise_id=noise_id,
                                    trial=trial,
                                    counts=counts.tolist(),
                                    available_us=[s.observation.available_us for s in result],
                                    start_us=[s.receipt.delivered_start_us for s in result],
                                    delivered=[
                                        list(s.receipt.delivered_current_pA) for s in result
                                    ],
                                    requested=[
                                        list(s.receipt.requested_current_pA) for s in result
                                    ],
                                    noise_hashes=engine.noise_hashes.copy(),
                                )
                            )
                        split_features[split] = {
                            key: np.array(value) for key, value in collected.items()
                        }
                        np.savez_compressed(
                            output / f"{prefix}_{split}_features.npz",
                            symbols=values,
                            **split_features[split],
                        )
                        atomic_json(output / f"{prefix}_{split}_records.json", trial_records)
                        split_costs[split] = time.perf_counter() - split_start
                        atomic_json(
                            output / "progress.json",
                            dict(network=network, condition=condition, delay=delay, split=split),
                        )
                        check_resources(output)
                    labels = {key: value[:, 0] for key, value in split_symbols.items()}
                    rows = []
                    for representation in ["final", "history", "cue_end", "distractor_end"]:
                        data = [split_features[split][representation] for split in SPLIT_SIZES]
                        row = save_prediction(
                            output,
                            prefix,
                            representation,
                            *data,
                            labels["fit"],
                            labels["validation"],
                            labels["test"],
                        )
                        rows.append(row)
                    # The input-history controls explicitly receive both symbols.
                    for name in ["C2", "C3", "C4", "C5", "C6"]:
                        data = []
                        for split_index, split in enumerate(SPLIT_SIZES):
                            values = split_symbols[split]
                            if name == "C2":
                                matrix = np.zeros((len(values), 4))
                            elif name == "C3":
                                matrix = values.astype(float)
                            elif name == "C4":
                                matrix = np.column_stack((values, values[:, 0] * values[:, 1]))
                            elif name == "C5":
                                order = generator(
                                    network, 203, delay_index, split_index
                                ).permutation(len(values))
                                matrix = split_features[split]["final"][order]
                            else:
                                matrix = split_features[split]["final"]
                            data.append(matrix)
                        fit_labels = labels["fit"]
                        validation_labels = labels["validation"]
                        if name == "C6":
                            fit_labels = generator(network, 204, delay_index, 0).permutation(
                                fit_labels
                            )
                            validation_labels = generator(network, 204, delay_index, 1).permutation(
                                validation_labels
                            )
                        row = save_prediction(
                            output,
                            prefix,
                            name,
                            *data,
                            fit_labels,
                            validation_labels,
                            labels["test"],
                        )
                        if name == "C2" and row["accuracy"] != 0.5:
                            raise RuntimeError("Current-only leakage gate")
                        rows.append(row)
                    for task in ["match", "parity"]:
                        task_labels = {
                            key: (
                                (value[:, 0] == value[:, 1]).astype(int)
                                if task == "match"
                                else np.bitwise_xor(value[:, 0], value[:, 1])
                            )
                            for key, value in split_symbols.items()
                        }
                        data = [split_features[split]["final"] for split in SPLIT_SIZES]
                        rows.append(
                            save_prediction(
                                output,
                                prefix,
                                task,
                                *data,
                                task_labels["fit"],
                                task_labels["validation"],
                                task_labels["test"],
                            )
                        )
                    all_rates = np.concatenate(activity)
                    record = dict(
                        network=network,
                        condition=condition,
                        delay_ms=delay,
                        models=rows,
                        representation=representation_diagnostics(split_features["fit"]["final"]),
                        activity_mean_hz=all_rates.mean(axis=0).tolist(),
                        activity_max_hz=float(all_rates.max()),
                        construction_s=build_s,
                        split_costs_s=split_costs,
                        provenance=engine.provenance(),
                        **check_resources(output),
                    )
                    summary.append(record)
                    atomic_json(output / "results_partial.json", summary)
                # Separately declared continuous binary lag-classification probe.
                reset_trial(engine, 149900, condition == "C0")
                binary = generator(network, 210).permutation(np.tile([0, 1], 128))
                commands = []
                for index, value in enumerate(binary):
                    current = np.zeros(4)
                    current[value] = 30
                    commands.append(
                        Command(
                            engine.config.trial_id,
                            str(index),
                            index * 20000,
                            tuple(float(x) for x in current),
                        )
                    )
                memory = engine.run_commands(commands)
                matrix = np.array([x.observation.rates_hz for x in memory])
                lag_results = []
                for lag in [1, 2, 4, 8]:
                    target = binary[np.arange(16, 256) - lag]
                    row = save_prediction(
                        output,
                        f"{network}_{condition}",
                        f"lag{lag}",
                        matrix[16:144],
                        matrix[144:192],
                        matrix[192:256],
                        target[:128],
                        target[128:176],
                        target[176:],
                    )
                    lag_results.append(row)
                np.savez_compressed(
                    output / f"{network}_{condition}_binary_stream.npz",
                    inputs=binary,
                    features=matrix,
                )
                atomic_json(output / f"{network}_{condition}_lag_results.json", lag_results)
            finally:
                engine.close()
    atomic_json(output / "results.json", summary)
    atomic_json(
        output / "resources.json",
        dict(
            elapsed_s=time.perf_counter() - started, simulated_s=244.48, **check_resources(output)
        ),
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
