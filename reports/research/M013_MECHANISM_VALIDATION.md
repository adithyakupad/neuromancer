# M013 mechanism qualification

Base05ad832c7c062ba5cdd8d1d9e38129410ecafa32; protocol commitffc5c7b8.
Mechanism implementation3bc283a2; scalar-boundary correctionf740b9d9.
Only additive modules/tests/scripts were introduced. The existing V1 source,
scientific archives and supervisor were not rewritten.

## Executed checks

`PYTHONPATH=src MPLCONFIGDIR=/tmp/m013-mpl /tmp/neuromancer-m011-v1-env/bin/python -m pytest tests/test_plasticity.py tests/test_functional_learning.py -q`

Ten tests passed,8warnings,3.09s. Includes real Brian pair timing versus independently
calculated exponentials for pre→post,post→pre,same-slot and100us-separated spikes;
positive/negative/zero reward; disabled updates; finite-value rejection; clipping;
reference checkpoint; original versus instrumented neural observations; exact
trace replay and weight restoration; balanced task energy/slew; readout test-label
mutation; nonlinear input-history solution. Initial whole-suite run205passed,
38warnings,42.48s; final exact-code suite recorded separately in final_tests.log/XML.
Warnings and failed early commands remain in raw evidence.

`Eligibility.event` is an independent scalar reference. `PlasticReservoir` adds
non-delivering Brian synapses matching E/E endpoints and arrival delays; original
synapses alone deliver neural current. Event-driven traces are stale between
spikes, so `eligibility()` explicitly decays from Brian's lastupdate to reward time.
The exact version's implementation is documented at
[Brian2 2.10.1 source](https://brian2.readthedocs.io/en/2.10.1/_modules/brian2/synapses/synapses.html)
(accessed2026-11-04); no later-version capability is presumed.

## Preserved unsuccessful development attempts

An initial test used a nonexistent helper name. A subsequent construction failed
because `e` is a Brian reserved constant. Corrected identifier `eligibility` leaves
mathematics unchanged. Direct Python dataclass equality also rejects identical NaN
filter initialization fields; fieldwise exact array checks including NaN masks
now compare all observation fields. These are not discarded scientific trials.
First pilot worker rejected NumPy float commands before integration; conversion to
plain float preserves numeric values. Original absolute deadline was reused.

## Limits

Tests cover explicit examples, not a proof across all spike histories. Plasticity
is a model assumption, not validated biology. E/E bounds and0.1pA learning rate
are declared engineering defaults. C2 is unmodulated eligibility-based pair STDP
with matched batch-update timing, not immediate event-wise classic STDP. C7 is
feature centering, not a causal activity-clamped reservoir. No claim of biological
learning or independent student authorship is made.

## Algorithm reading guide

- `decay`: exponential trace propagation; elapsed/tau are both milliseconds.
- `reward_update`: average trial reward×eligibility, multiply by pA learning rate,
  add to current weights and clip; disabled mode returns unchanged weights.
- `PlasticReservoir.learn`: only declared E/E weight indices can change.
- `schedule`: two symbols encoded by channel identity, with equal exposure and
  the original30pA slew limits; no target argument.
- `probe_fit`: derive scaling only from probe fitting, select ridge strength only
  with validation, then freeze coefficients.
- `m013_pilot.execute`: predict training output before using that label; update
  recurrent weights only after completed four-trial training minibatches. Replace
  training decoder with independently fit standardized probe decoder for scoring.
- `m013_analyze`: independently recompute held-out balanced accuracy, confusion,
  constraints, exposure and paired network statistics from saved artifacts.

## Final qualification closure

Final exact-production-code suite:211passed,46warnings,58.45s; no historical test was edited. Independent pair/noise/process cleanup verification PASS. Whole scientific evidence reproduction PASS. Pilot instrument engineering PASS is confined to this task/model configuration; confirmatory efficacy is NOT qualified. Not every conceivable malformed artifact or spike history is tested.
