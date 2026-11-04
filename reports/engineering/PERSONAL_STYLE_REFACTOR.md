# Personal coding style and readability refactor

## Scope and lineage

This is an engineering readability study, not a new scientific experiment.
The separate M009 reliability backport must qualify before this branch is
created. Its numerical code is the V1 reference; performance-branch ancestry is
not merged into V1. No merge, tag, publication or scientific acquisition is
part of this refactor. Exact source revisions and qualification evidence are
recorded in the accompanying manifest.

The student supplied an introductory MATLAB exam as style evidence. It was
visually inspected rather than relying on incomplete text extraction. Its printed
instructions were treated as document content, not user commands. PDF SHA256:
`cd83fde55dc2e641c16168e4a9a3a5cdde31951fb6de2b271d1c31c6e8f16e38`.
The PDF and personal identifiers are not redistributed. Observations: explicit
Boolean initialization and separate decisions (`sweetCombo`, PDF20), initialized
counters and direct iteration (`getCar`,24), named directional flags and result
masks (`exitStrategy`,40–41), and separated data/intermediate vectorized
calculations/sorting (`boxInventory`,45).

These are limited observations in an exam setting. Python naming, units,
exceptions and scientific testing derive from the user's explicit requirements
and project contracts. Exam errors, indexing limitations and inefficient Python
translations are not style prescriptions. The agent wrote the Python changes;
they are not represented as the user's personal authorship.

## Selected files and changes

| File | Reason for selection | Change |
| --- | --- | --- |
| `control.py` | PI decisions and actuator constraints are central interview topics. | Separate initialization, validity, aggregation and anti-windup steps; explicit ZERO/MAX/other initialization; name proposed integral. |
| `identify.py` | Explain AR/ARX fitting and causal recursive forecasts. | Expand dense statements; name rate/current histories, feature row, prediction list and predicted rate. |
| `online_identify.py` | Trace FIR features and RLS mathematics. | Expand decisions; expose residual; explain old-state updates and joint commit; preserve all windows/forgetting factors. |
| `predictive.py` | Trace observation-to-action order and estimator transactions. | Expand guards/state updates; expose RLS residual and dimensions; keep receipt validation, safe fallback and deadline calls intact. |

No production functions/classes/frameworks were added or removed. No public
signature, evidence field, model family, parameter shape or established scientific
term changed. Scientific operation ordering remains explicit and unchanged.

Neural engine, observation processing, performance-sensitive planner, supervisor, clocks,
runners and statistical analysis remain byte-identical to the qualified reference.
They were reviewed and explained in `docs/development/CODING_STYLE.md` rather than
rewritten for uniformity. No generated Brian code, third-party code, historical
snapshot, frozen protocol or numerical evidence was changed.

## Before and after

RLS previously packed related operations on one line:

```python
gain = self.p @ z / denominator; theta = self.theta + np.outer(gain, v - z @ self.theta)
p = (self.p - np.outer(gain, z @ self.p)) / .999; p = (p + p.T) / 2
```

The new version exposes the residual while retaining the exact arithmetic tree
and old-state ordering:

```python
gain = self.p @ z / denominator
residual = v - z @ self.theta
theta = self.theta + np.outer(gain, residual)
p = (self.p - np.outer(gain, z @ self.p)) / 0.999
p = (p + p.T) / 2
```

Initialization previously used a nested conditional expression:

```python
self.q = 0. if name == 'ZERO' else 120. if name == 'MAX' else calibration.feedforward_pA
```

It now makes the three controller cases visible:

```python
if name == "ZERO":
    self.q = 0.0
elif name == "MAX":
    self.q = 120.0
else:
    self.q = calibration.feedforward_pA
```

PI's `proposed` becomes `proposed_integral`; its clipping, outward-saturation
condition, retained integral and final action are on separate lines. ARX's
`ys`, `us`, `pred`, `value` become `rate_history`, `current_history`, `predictions`,
`predicted_rate`. Numerical vocabulary and compact matrix symbols are retained
where they directly express the equations. No dense calculation was reassociated.

## Readability evidence

| File | Before/after lines | Before/after maximum line length | Semicolons |
| --- | ---: | ---: | ---: |
| control |190/283|116/97|23/0|
| identify |125/243|187/98|17/0|
| online_identify |107/199|150/99|41/0|
| predictive |180/403|566/94|70/0|

There are151fewer multi-statement semicolons and the longest line falls from566
to99characters. Vertical length increases intentionally to make control flow
visible. These are objective readability proxies, not a measured user-comprehension
score. The function guide and independent explanation checklist address concepts
that automated tests cannot establish the user understands.

## Qualification methods

The prospective plan freezes exact output equality and performance tolerances
before production changes. Reference source hashes are recorded separately from
new source hashes; changing source is not falsely described as identical source
provenance. The original source remains intact in Git.

Black26.5.1 with Python3.12 target and100-column limit first produced an
AST-identical formatting draft. A separate verifier reverses *only* the declared
local-name, residual and initialization transformations, removes docstrings, and
requires identical operation trees. Golden outputs then independently require
identical dtype, shape and array bytes plus identical JSON values.

The fixture covers initial FIR fits/information, every declared online update
family, AR/ARX forecasts, whole-network bootstrap gates, all625planner scores
and predictions at five prior doses, fixed/adaptive commands and missing-input
events,2000PI observations including saturation/rearming, and a1s development0
neural replay. Full spike events and public counts match continuous/chunked
execution. This is an engineering smoke, not a fresh controller outcome study.
Controllers use only synthetic permitted records; private neural arrays are
accessed separately by the evaluator to compare replay. Golden controllers use
a deterministic clock; native-clock/failure tests qualify actual deadline behavior.

Performance uses three fixed ABBA cycles, twelve separate processes, nine raw
timing samples per workload/process, no excluded samples, one worker and a600s
global budget. Limits frozen before edits:≤10% paired-median and≤20% paired-p95
wall-time regression, peak RSS≤10% increase and inside supported resources.
Requested single-thread environment variables do not prove actual BLAS behavior.
First timing samples are first *measured* calls after fixture setup, not cold
interpreter/import benchmarks. No speedup claim is a scientific accuracy claim.

An initial unprivileged harness dry run correctly failed to establish native
boot-clock identity; it was rerun with normal host access, not by weakening the
clock. Preserve that attempt separately. No production test failure is hidden.

## Scientific record and interpretation

Frozen PI11.46875, RLS-MPC13.12921875 and fixed-MPC18.9778125Hz·s remain the
development post-loss cumulative errors. Adaptive superiority over PI remains
FAIL. V0.1/V0.2 failures, M003.1/M003.2 negative findings, M004 identification
versus detection distinctions, M005A.5 short-horizon failure and M005A.7 extended
PI success remain historical results with their original scope. Validation and
locked100–119 remain unopened. No biological learning, plasticity, living-neuron
control, hardware-safe stimulation or hard-real-time claim is added.

See `docs/development/CODING_STYLE.md` for concise function-by-function explanations
and the remaining independent-understanding checklist. A human review remains
valuable: the agent can verify equations and organization, but cannot certify
the user's ability to independently derive or defend every algorithm.

## Executed results and reproducible commands

Starting workspace: `08a956ce4548e1f16af568dd247f40d7d9505f7d` on engineering/m008-supervisor-diagnosis.
Qualified V1 base: `86ad99f6956c76a5bb6d169e21544684f57c9270`; numerical/backport source `24f043900b5a7b36b90a19aa81114bb4a5b3e458`.
Review branch: `refactor/personal-code-style`. Reference plan/outputs committed at ca53ea54 and cf195470 before production edits.
The final commit identity is supplied in the handoff; the accompanying hashes identify the exact qualified implementation independently of later evidence-only commits.

Full post-application regression: **200 passed, 25 warnings, no skips, 65.78s**. Earlier isolated-draft suite:200passed/25warnings/65.51s. Existing Brian/pyparsing deprecations are retained in full logs.
Exact comparison: **91 arrays** (dtype, shape, bytes) plus canonical JSON records, including spikes/counts, FIR/ARX/RLS states, PI trajectories and all candidate outputs. The independent operation-tree verifier accepts only the declared transformations.
Preservation:38,055base files checked;38,051unchanged, only the four declared numerical-source readability edits. No historical source/evidence/protocol was rewritten.

Actual commands (from repository root; fresh output directories):
```sh
PYTHONPATH=src .venv/bin/python tools/verify_personal_style_ast.py 86ad99f6 src/neuromancer NEW_AST.json
PYTHONPATH=src .venv/bin/python tools/verify_personal_style_preservation.py 86ad99f6 NEW_PRESERVATION.json
PYTHONPATH=src .venv/bin/python tools/personal_style_probe.py NEW_PROBE --neural --reference reports/engineering/evidence/personal_style/reference
PYTHONPATH=src .venv/bin/python tools/qualify_personal_style.py --output NEW_QUALIFICATION
```
The actual interpreter was `/tmp/neuromancer-m007-20261101/bin/python`, CPython3.12.15 with the unchanged pinned research dependencies. The executed qualifier (archived as `final/qualifier_executed.py`) used its fresh `final/` root. The current repeat helper requires `--output` so committed evidence cannot be overwritten; this argument-only tooling repair was checked with `--help`. Do not overwrite committed evidence. Complete executed commands are in `final/commands.json`; full logs/XML and supervision outcomes are retained.

### Paired performance

Apple M5,10logical CPUs,16GiB,macOS26.5.2 arm64; one worker. Three ABBA cycles;54samples per version/workload. All twelve runs exactly match reference arrays and records. No sample was removed.
| Workload | Reference median / p95 ms | Refactor median / p95 ms | Median / p95 ratio |
| --- | ---: | ---: | ---: |
| fir_1000_predictions | 9.742 / 10.217 | 9.701 / 9.896 | 0.996 / 0.969 |
| rls_100_updates | 4.168 / 4.621 | 4.091 / 4.491 | 0.981 / 0.972 |
| planner_625_candidates | 8.888 / 9.631 | 8.574 / 9.315 | 0.965 / 0.967 |
| pi_1000_observations | 5.742 / 5.991 | 5.697 / 5.935 | 0.992 / 0.991 |
| arx_fit | 3.727 / 4.087 | 3.691 / 4.022 | 0.990 / 0.984 |

Whole-process peak RSS: reference944.05MiB, refactor945.48MiB (+0.152%), below2GiB. This includes retained golden arrays and neural fixture; it is not per-kernel allocation volume. Every paired-cycle median and p95 also stays inside the frozen10%/20% limits. Shared600s benchmark completed with517.972sremaining; cleanup verified.
Small timing differences are normal variability, **not a claimed optimization**. The unchanged planner also varies, illustrating that limitation. This finite local sample supports no material regression on these fixtures, not universal hardware or hard-real-time guarantees.


## Final local decision and release boundary

**Local engineering PASS.** Full1200s qualification completed with967.696sremaining;
installation/import/smoke/pip-check completed under the *same* original deadline,
with862.233sremaining. The wheel is1.0.0; installation was noneditable, source
PYTHONPATH was removed, and all four site-packages files match current source
bytes. No scientific dependency or metadata version changed.

Post-refactor evidence-only reproduction again gives byte-identical four canonical
numerical outputs and four PNG/SVG figures; both independent verifiers pass.
No new study, reserved outcome, neural parameter or controller algorithm was used.
The1s replay and installed200ms smoke are development-only instrument fixtures.

The code/AST/equivalence/performance/local-test gates pass. Hosted Linux/macOS
qualification on the review revision remains a separate mandatory closing gate;
record actual run IDs/outcomes in the closing evidence and handoff, never infer
success from the earlier M009 branch. No merge/tag/publication is authorized.
The reliability-only V1 branch can be reviewed independently of this style branch.

Remaining limitations: bitwise equality is qualified on the pinned local stack,
finite engineering timings do not prove all-machine throughput, hosted Intel
macOS does not establish hosted Apple Silicon behavior, and personal explanation
skills require the user's independent review. These do not revise the historical
scientific outcomes. Review FIR lag construction, the old-state RLS update,
anti-windup, partial observations and network-level replication before modifying
this instrument. The next step is review, not a new controller experiment.

## Hosted closing gate and final recommendation

**Engineering PASS** for implementation commit
`d028b089aebee1369b7beffb0122851bd7df1bac`, on
`refactor/personal-code-style`. Hosted package/regression run
[41893766820](https://github.com/adithyakupad/neuromancer/actions/runs/41893766820)
passed ubuntu-latest and macos-15-intel, with all200tests,35real-process probes,
pinned dependency checks, wheel installation and installed smoke. Legacy run
[41893766843](https://github.com/adithyakupad/neuromancer/actions/runs/41893766843)
also passed. Full raw logs and structured job results are retained in `hosted/`.
The separate M009 closing revision86ad99f6 passed run41892453628 on both platforms.
The two arm64 runner-acquisition failures remain preserved and are not counted
as successful hosted-arm64 tests.

This closing commit changes evidence/reporting only; all production and helper
source hashes remain identical to the fully qualified implementation. Final
closing-revision CI is independently required before merge, and its exact commit
and checks are provided in the handoff. The report cannot embed its own containing
commit hash without changing that hash; use `git rev-parse HEAD` on this branch.

Review the four-file code change with:

```sh
git diff 86ad99f6..HEAD -- src/neuromancer docs/development/CODING_STYLE.md
```

Raw verification archives are isolated under `evidence/personal_style/`; they are
synthetic/development instrument evidence, not additional independent research
cohorts. No numerical finding, controller superiority claim, publication state or
V1 scientific scope changed. Ready for independent review, not automatic merge,
tag or publication. User comprehension and authorship are not inferred from PASS.
