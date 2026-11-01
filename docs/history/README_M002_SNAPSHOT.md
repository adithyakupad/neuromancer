# Neuromancer

> Build a programmable, stimulation-responsive neural system for closed-loop biological-computing experiments.

## Thesis

Build a programmable, stimulation-responsive neural system for closed-loop biological-computing experiments.

## Planned stack

- Python
- Cortical Labs SDK
- electrophysiology
- spiking models
- plasticity
- closed-loop control

## Milestones

- [x] Define neural state and stimulation interfaces
- [ ] Implement a model-backed simulator source
- [ ] Add plasticity / state adaptation
- [ ] Benchmark closed-loop controllers
- [ ] Design a CL1-compatible experiment interface

## Status

**Brian2 substrate implemented; frozen V0 control-authority gate failed.**

Mission 002 separates passing software qualification from insufficient measured
control authority. System identification and controller evaluation have not begun.

This repository is part of an ongoing research-engineering project backlog. Claims, results, and benchmarks will be added only when supported by reproducible experiments.

## Principles

- Start with explicit scientific or engineering questions.
- Establish simple baselines before adding complex models.
- Use quantitative evaluation and documented failure modes.
- Preserve reproducibility through versioned data, configuration, and experiment outputs.
- Separate demonstrated results from planned capabilities.

## Mission 002: simulation substrate

The first implementation provides the frozen 1,000-cell Brian2 E/I LIF model,
process-isolated trials, constrained held-current actions, partial spike counts,
and exact same-environment replay. It does not implement identification or control.
Qualification and scientific feasibility are separate: see
[Mission 002 report](reports/M002_BRIAN_SUBSTRATE.md) for the measured decision.

Python **3.12** is required. Keep environments separate from historical audits:

```sh
python3.12 -m venv /tmp/neuromancer-m002
/tmp/neuromancer-m002/bin/python -m pip install -r requirements-m002.txt
/tmp/neuromancer-m002/bin/python -m pip install --no-build-isolation --no-deps -e .
/tmp/neuromancer-m002/bin/python -m pip check
/tmp/neuromancer-m002/bin/python -m pytest -q
/tmp/neuromancer-m002/bin/neuromancer-diagnostic --mode smoke --output runs/my-smoke
```

The dependency lock includes optional plotting/test tools. The minimal installed
runtime needs only the dependencies in pyproject.toml. Public use:

```python
from neuromancer import Command, Config, Trial

# Use a script with this guard: trials use spawned worker processes.
if __name__ == "__main__":
    with Trial(Config(trial_id="example")) as trial:
        action = Command("example", "pulse-0", 0, (30.0, 30.0, 30.0, 30.0))
        result = trial.advance(action, stop_us=20_000)
        print(result.observation.counts)  # 20 virtual recording channels
```

Currents are pA of model-injected current, never electrode µA. Actions start only
at the current trial boundary. Invalid actions raise ValueError atomically;
`advance(None, ...)` ramps the previous current toward zero by at most30 pA per
channel. Each step returns a delivery receipt and completed half-open spike bin.
`reset()` restores the fresh episode; `close()` is idempotent. Returned tuples are
immutable and contain no hidden neural state or neuron identities. Python private
attributes are not an adversarial security sandbox; the state boundary is the
separate worker process and its restricted message protocol.

The 100 µs neural clock and20 ms stimulation/observation clock are distinct.
Spike times refer to Brian's threshold scheduler slot, not a substep estimate of
continuous threshold crossing. The causal100 ms rate filter is unavailable (NaN)
until the prescribed baseline ends at15 s, when it initializes from [7,15) s.
Raw channel counts/rates remain available from the first bin. Missing recording
coverage uses masks, -1 counts and NaN rates in evaluator fixtures; zero spikes
with full coverage remain valid zeros. No raw analog signal is synthesized.

Evaluator-only diagnostics (fresh output directory required):

```sh
neuromancer-diagnostic --mode authority --output runs/my-authority
neuromancer-diagnostic --mode convergence --output runs/my-convergence
neuromancer-diagnostic --mode performance --output runs/my-performance
```

Authority uses all ten training networks and paired5 s sham/stimulation holds
following the frozen5 s burn-in and10 s baseline. It does not fit a controller.
Convergence uses nested OU innovations at100/50 µs; performance measures four
fresh-process retention/chunking cases. These take longer than the smoke test.
Each run writes provenance, numerical outputs and terminal status; figures use
fixed styles and no generation date. The worker's default spike storage is
cleared after each integration segment; evaluator retention is explicitly opt-in.
Large NPZ arrays remain under ignored runs/. Curated numerical summaries and
figures are committed under reports/evidence/m002/.

Random streams use SeedSequence roles0–7 from V0. Roles0–3 always use replicate0.
OU blocks use key(network,4,replicate,one-second-block) and PCG64;50 µs innovations
are paired into the100 µs stream by the exact OU composition rule. Thus different
commands/spike histories cannot alter exogenous noise consumption. Brian has no
implicit random expression in this model; role7 is reserved rather than mutating
a global generator. Exact replay is qualified within the recorded environment;
bitwise cross-version or cross-platform equivalence is not promised.
