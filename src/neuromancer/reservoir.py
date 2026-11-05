"""M014 frozen-memory task. Decoder inputs are recorded counts, never labels."""
from dataclasses import replace
import numpy as np
from .substrate import Command
from .functional_learning import probe_fit, probe_predict, balanced_accuracy

DELAYS_MS = (20, 40, 80, 160)
SPLIT_SIZES = {'fit': 16, 'validation': 8, 'test': 16}


def generator(network, role, delay_index=0, split_index=0):
    seed = np.random.SeedSequence(20261105, spawn_key=(network, role, delay_index, split_index))
    return np.random.default_rng(seed)


def symbols(network, delay_index, split_index, size):
    if size % 4:
        raise ValueError('Factorial balance requires multiples of four')
    cue = np.repeat([0, 1], size // 2)
    cue = generator(network, 200, delay_index, split_index).permutation(cue)
    distractor = np.zeros(size, dtype=int)
    distractor_rng = generator(network, 201, delay_index, split_index)
    for label in (0, 1):
        members = np.flatnonzero(cue == label)
        values = np.tile([0, 1], len(members) // 2)
        distractor[members] = distractor_rng.permutation(values)
    order = generator(network, 202, delay_index, split_index).permutation(size)
    return np.column_stack((cue, distractor))[order]


def commands_for_trial(cue, distractor, delay_ms, trial_id):
    if cue not in (0, 1) or distractor not in (0, 1) or delay_ms not in DELAYS_MS:
        raise ValueError('Invalid task')
    delay_bins = delay_ms // 20
    rows = np.zeros((10 + 2 * delay_bins, 4))
    rows[:4, cue] = [30., 60., 30., 0.]
    second_start = 4 + delay_bins
    rows[second_start:second_start + 4, 2 + distractor] = [30., 60., 30., 0.]
    commands = [Command(trial_id, str(index), index * 20000,
                        tuple(float(value) for value in row)) for index, row in enumerate(rows)]
    return commands


def features(completed, stop_us):
    if len(completed) < 4:
        raise ValueError('Four completed bins required')
    for result in completed:
        observation = result.observation
        if observation.available_us > stop_us or observation.stop_us > stop_us:
            raise ValueError('Future observation')
        if not all(observation.valid):
            raise ValueError('Missing observation')
    last = completed[-4:]
    for index, result in enumerate(last):
        if result.observation.stop_us != stop_us - (3 - index) * 20000:
            raise ValueError('Noncontiguous observation window')
    counts = np.array([result.observation.counts for result in last], dtype=float)
    final_rates = counts[-2:].sum(axis=0) / (5 * .04)
    recent_rates = (counts / (5 * .02)).ravel()
    return final_rates, recent_rates


def set_recurrence(engine, enabled):
    for synapse in engine.synapses:
        synapse.active = bool(enabled)


def reset_trial(engine, replicate_id, enabled):
    engine.restore('initial')
    engine.config = replace(engine.config, replicate_id=replicate_id)
    set_recurrence(engine, enabled)


def score_readout(fit_x, validation_x, test_x, fit_y, validation_y):
    fitted = probe_fit(fit_x, fit_y, validation_x, validation_y)
    predictions = probe_predict(test_x, fitted)
    return fitted, predictions


def representation_diagnostics(matrix):
    centered = matrix - matrix.mean(axis=0)
    covariance = centered.T @ centered / max(1, len(matrix) - 1)
    eigenvalues = np.maximum(np.linalg.eigvalsh(covariance), 0)
    squared = float(eigenvalues @ eigenvalues)
    dimension = float(eigenvalues.sum() ** 2 / squared) if squared else 0.
    return dict(rank=int(np.linalg.matrix_rank(centered)), effective_dimension=dimension,
                covariance=covariance.tolist(), mean_rate_hz=float(matrix.mean()),
                maximum_rate_hz=float(matrix.max()))
