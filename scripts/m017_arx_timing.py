"""Bounded standalone timing of the M017 50-step ARX forecast fixture."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np
from neuromancer.identify import fit
from neuromancer.supervisor import Deadline, atomic_json


def main(output):
    deadline = Deadline.from_environment()
    rng = np.random.default_rng(20261104)
    inputs = rng.uniform(0, 30, (3300, 4))
    rates = np.full((3300, 4), 8.0)
    for index in range(1, len(rates)):
        rates[index] = (
            8 + .4 * (rates[index - 1] - 8) + .002 * inputs[index] + rng.normal(0, .02, 4)
        )
    model = fit(rates, inputs, "ARX", 4)
    wall, cpu = [], []
    for _ in range(9):
        deadline.check()
        started = time.perf_counter_ns()
        cpu_started = time.process_time_ns()
        prediction = model.forecast(rates[:3200], inputs[:3200], inputs[3200:3250])
        cpu.append(time.process_time_ns() - cpu_started)
        wall.append(time.perf_counter_ns() - started)
    atomic_json(output, dict(
        wall_ns=wall, cpu_ns=cpu, shape=list(prediction.shape), dtype=str(prediction.dtype),
        forecast_sha256=hashlib.sha256(prediction.tobytes()).hexdigest(),
        peak_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    ))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
