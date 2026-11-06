"""Frozen M013 pilot acquisition; run only after mechanism/resource gates."""

import json
import os
from pathlib import Path
import resource
import sys
import time
import numpy as np
from neuromancer.functional_learning import (
    balanced_symbols,
    schedule,
    ridge_fit,
    predict,
    probe_fit,
    probe_predict,
    balanced_accuracy,
)
from neuromancer.plasticity import PlasticReservoir
from neuromancer.substrate import Config
from neuromancer.supervisor import Deadline, atomic_json


def execute(output):
    deadline = Deadline.from_environment()
    all_rows = []
    for network in [13000, 13001]:
        split_rng = np.random.default_rng(
            np.random.SeedSequence(20261104, spawn_key=(network, 100))
        )
        splits = {
            name: balanced_symbols(count, split_rng)
            for name, count in [
                ("train", 32),
                ("probe", 16),
                ("validation", 8),
                ("test", 16),
                ("delay20", 8),
                ("delay100", 8),
            ]
        }
        for condition in range(5):
            deadline.check()
            reservoir = PlasticReservoir(
                Config(
                    network_id=network,
                    replicate_id=1300,
                    root_seed=20261104,
                    trial_id=f"m013-{network}-{condition}",
                )
            )
            reservoir.enabled = True
            initial = reservoir.weights()
            eligibility = []
            rewards = []
            training_x = []
            training_y = []
            features = {}
            targets = {}
            receipts = []
            learning = []
            control_rng = np.random.default_rng(
                np.random.SeedSequence(20261104, spawn_key=(network, 101))
            )
            train_labels = np.bitwise_xor(splits["train"][:, 0], splits["train"][:, 1])
            random_labels = control_rng.permutation(train_labels)
            try:
                for phase, symbols in splits.items():
                    if phase != "train":
                        reservoir.enabled = False
                    phase_weights = reservoir.weights()
                    features[phase] = []
                    targets[phase] = []
                    for index, (a, b) in enumerate(symbols):
                        deadline.check()
                        if Path(os.environ["NEUROMANCER_STOP_FILE"]).exists():
                            raise RuntimeError("Cooperative resource stop")
                        delay = 20 if phase == "delay20" else 100 if phase == "delay100" else 40
                        commands, response = schedule(
                            int(a),
                            int(b),
                            delay,
                            reservoir.engine.time_us,
                            reservoir.engine.config.trial_id,
                        )
                        observations = reservoir.engine.run_commands(commands)
                        feature = np.mean(
                            [x.observation.sector_rate_hz for x in observations[response]], axis=0
                        )
                        if not np.all(np.isfinite(feature)):
                            raise RuntimeError("Invalid response")
                        features[phase].append(feature)
                        targets[phase].append(int(a ^ b))
                        for step in observations:
                            receipts.append(
                                dict(
                                    start_us=step.receipt.delivered_start_us,
                                    stop_us=step.receipt.delivered_stop_us,
                                    requested=list(step.receipt.requested_current_pA),
                                    delivered=list(step.receipt.delivered_current_pA),
                                    counts=list(step.observation.counts),
                                    phase=phase,
                                    trial=index,
                                )
                            )
                        if phase == "train":
                            label = int(random_labels[index]) if condition == 4 else int(a ^ b)
                            if training_x:
                                coefficients = ridge_fit(
                                    np.array(training_x), np.array(training_y), 1.0
                                )
                                prediction = (
                                    float(predict(feature[None, :], coefficients)[0]) >= 0.5
                                )
                            else:
                                prediction = False
                            reward = 1 if prediction == label else -1
                            training_x.append(feature)
                            training_y.append(label)
                            learning.append(
                                dict(trial=index, reward=reward, correct=bool(prediction == label))
                            )
                            eligibility.append(reservoir.eligibility())
                            rewards.append(reward)
                            if len(rewards) == 4:
                                modulator = np.ones(4) if condition == 2 else np.array(rewards)
                                if condition == 3:
                                    modulator = control_rng.permutation(modulator)
                                if condition != 0:
                                    reservoir.learn(eligibility, modulator)
                                eligibility = []
                                rewards = []
                        elif not np.array_equal(phase_weights, reservoir.weights()):
                            raise RuntimeError("Evaluation weight mutation")
                    features[phase] = np.array(features[phase])
                    targets[phase] = np.array(targets[phase])
                    atomic_json(
                        output / "progress.json",
                        dict(network=network, condition=condition, phase=phase, completed=True),
                    )
                fit = probe_fit(
                    features["probe"],
                    targets["probe"],
                    features["validation"],
                    targets["validation"],
                )
                predictions = {
                    phase: probe_predict(features[phase], fit)
                    for phase in ["test", "delay20", "delay100"]
                }
                row = dict(
                    network=network,
                    condition=f"C{condition}",
                    accuracy=balanced_accuracy(targets["test"], predictions["test"]),
                    delay20=balanced_accuracy(targets["delay20"], predictions["delay20"]),
                    delay100=balanced_accuracy(targets["delay100"], predictions["delay100"]),
                    changed=int(np.sum(initial != reservoir.weights())),
                    bounds=float(np.mean((reservoir.weights() == 0) | (reservoir.weights() == 30))),
                )
                # C7 is a diagnostic feature normalization, not a changed neural model.
                centered = {
                    key: value - value.mean(axis=1, keepdims=True)
                    for key, value in features.items()
                }
                centered_fit = probe_fit(
                    centered["probe"],
                    targets["probe"],
                    centered["validation"],
                    targets["validation"],
                )
                row["C7_accuracy"] = balanced_accuracy(
                    targets["test"], probe_predict(centered["test"], centered_fit)
                )
                all_rows.append(row)
                prefix = output / f"{network}_C{condition}"
                np.savez_compressed(
                    str(prefix) + ".npz",
                    initial_weights=initial,
                    final_weights=reservoir.weights(),
                    coefficients=fit[2],
                    mean=fit[0],
                    scale=fit[1],
                    **{f"x_{k}": v for k, v in features.items()},
                    **{f"y_{k}": v for k, v in targets.items()},
                    **{f"prediction_{k}": v for k, v in predictions.items()},
                    **{f"symbols_{k}": v for k, v in splits.items()},
                )
                atomic_json(
                    Path(str(prefix) + ".json"),
                    dict(
                        metrics=row,
                        receipts=receipts,
                        learning=learning,
                        selected_alpha_index=fit[3],
                        validation_scores=fit[4],
                        provenance=reservoir.engine.provenance(),
                    ),
                )
                atomic_json(output / "results_partial.json", all_rows)
                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                rss_bytes = rss if sys.platform == "darwin" else rss * 1024
                if (
                    rss_bytes > 2 * 1024**3
                    or sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
                    > 200 * 1024**2
                ):
                    raise RuntimeError("Declared resource ceiling exceeded")
            finally:
                reservoir.close()
        baseline = {}
        for name in ["C5", "C6_linear", "C6_nonlinear"]:
            inputs = {}
            for phase, symbols in splits.items():
                if name == "C5":
                    inputs[phase] = symbols[:, 1:2]
                elif name == "C6_linear":
                    inputs[phase] = symbols
                else:
                    inputs[phase] = np.column_stack((symbols, symbols[:, 0] * symbols[:, 1]))
            fit = probe_fit(
                inputs["probe"], targets["probe"], inputs["validation"], targets["validation"]
            )
            baseline[name] = balanced_accuracy(targets["test"], probe_predict(inputs["test"], fit))
        atomic_json(output / f"{network}_input_baselines.json", baseline)
    atomic_json(output / "results.json", all_rows)


if __name__ == "__main__":
    execute(Path(sys.argv[1]))
