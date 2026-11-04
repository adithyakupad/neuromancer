# M011 — performance qualification review

**Review complete; optional style qualification HOLD and V1.1 HOLD remain.**
No new comparative timing benchmark, optimization, source modification or gate
approval was performed. The existing failed M010 gates remain FAILED. Isolated
V1 has its own original release gates and must not inherit these optional targets.

## Evidence and units of analysis

Read both committed M010banks: performance/ and performance_serialized/. Each
has12processes,threeABBAcycles,6processes/source,9measurements/process/workload:
54samples/source/workload. All1080wall samples and1080paired CPU samples across
five workloads/two banks remain included. Their source trees and numerical outputs
are identical; this is effectively a same-source placebo comparison, not evidence
that a code change caused a slowdown. Each process holds repeated correlated
measurements;54is not54independent replication units.

Raw inputs are hashed in `evidence/m011/performance_review/analysis/analysis.json`.
Analysis code:tools/m011_performance_review.py. Descriptive whole-cycle bootstrap:
seed20261111,10000draws, THREE blocks only. Three draws from three cycles produce
only ten unordered count mixtures; extra resamples do not create new information.
Intervals below are exploratory precision diagnostics, not new pass/fail criteria
or a calibrated population-coverage guarantee.

| Bank / workload | Original p95ratio | Descriptive cycle-bootstrap95range |
| --- | ---: | ---: |
| performance / fir_1000_predictions | 1.627 | [0.852, 3.161] |
| performance / rls_100_updates | 1.584 | [0.951, 2.185] |
| performance_serialized / fir_1000_predictions | 1.296 | [0.880, 1.753] |
| performance_serialized / rls_100_updates | 1.231 | [1.050, 1.605] |

## Confound and variance assessment

- First bank:qualified-clock records prove17.897sof overlap with wheel-install
  verification in the last current/reference cases. FIR's largest current wall-
  minus-CPU interval is49.176ms. It is a confounded failed measurement, not a
  discarded sample or evidence that installation explains every tail observation.
- Serialized bank:agent-owned concurrent work was avoided, but historical system
  load, frequency/thermal state, E/Pcore placement, affinity and per-operation
  thread activity were not recorded. No claim of an idle host is justified.
  FIR/RLS maximum wall-minus-CPU gaps are10.906/3.779ms in current cases versus
 1.502/.392ms reference. Off-CPU gaps include scheduling or waiting; they do
  not uniquely identify a cause. CPU-time variability also matters.
- Ordering:fixedABBAis counterbalancing, not randomized source assignment. RLS
  serialized cycle p95ratios1.054,1.570,1.194show process/context heterogeneity.
  The descriptive RLS interval excludes1 in this small sample, but identical
  source prevents attributing that association to a changed algorithm. Paths,
  imports/heap layout, scheduling and other context are not identical treatments.
- Startup:imports/fixture construction precede timed kernels. First measured
  calls are NOT cold interpreter-start measurements. Source extraction/cache and
  process startup may affect later state, but their latency is not included in
  the reported function blocks.
- Warm-up/state:RLSreuses an evolving estimator over repeated100-update blocks.
  The first block checks information at received1,50,100; subsequent blocks check
  twice. This follows unchanged production code. First-versus-later samples mix
  initialization/check cadence with warm-up; neither may be removed post hoc.
  Pair comparisons by process and update phase in a future protocol.
- Precision:p95over54pooled values is determined by a few high-order observations.
  Pooling hides six process clusters and three temporal blocks. Medians near1
  and exact source equality do not make the failed p95point gates pass.

## BLAS and environment observations

Two small CURRENT metadata probes, default environment and requested1thread,
are preserved as blas_default.json/blas_requested_one.json. NumPy2.5.4 reports
AppleAccelerate BLAS/LAPACK. threadpoolctl is unavailable. Requests are explicitly
None versus1, but actual active threads are NOT MEASURED. Current build metadata
cannot reconstruct M010thread counts. Process CPU includes native threads and is
not an inferred single-core measurement. No dependency was added or upgraded.
The8x8backend initialization has no latency score and is not a benchmark.

Release numerical verification reuses an unchanged golden-output harness which
incidentally records its fixed microtimings. Those incidental StageD timings are
retained but NOT used in this review, as a new relative benchmark, or to clear
M010's failed gates. No source version was selected from favorable outcomes.

## Prospective recommendation — not approved or executed

Keep the existing<=10%median/<=20%p95/<=10%RSS gates and all past failures active
until a separately justified protocol is approved BEFORE data acquisition.
A future proposal should:

1. Separate exact functional equivalence, the unchanged250msplanner release
   deadline, and statistical speed/regression claims. None substitutes for another.
2. Calibrate same-source false-failure/precision first, with fixed sample count,
   process-level pairing, source/order blinding or randomized counterbalancing,
   and a declared resource cap. Freeze stopping rules; no retries until green.
3. Treat process/cycle as blocks; retain every measured sample. Record load,
   CPU/wall, runtime/build, affinity/thermal information if genuinely available,
   actual supported thread observations and concurrent-task intervals.
4. Prespecify separate cold-start, warmed operation and stateful-update workloads.
   If resetting RLS state, do it outside the timed region and use identical state
   and update indices for both variants. Preserve the real information-check cadence.
5. Choose sample size from both observed failed banks' between-block variance and
   a declared interval-width goal. A possible budgeted starting design is20paired
   process blocks with100measurements/block, but this is a proposal requiring a
   forecast and independent preregistration, not a new accepted gate or study.
6. Report absolute latencies and uncertainty beside ratios; ambiguous comparisons
   remain inconclusive. Do not lower thresholds just to make optional work pass.

## Separate readiness conclusions

- Personal style:still HOLD under its declared outstanding qualification; this
  review does not approve an alternate protocol or reinterpret failed M010points.
- V1.1:performance/v1-1-optimization ce147866 remains HOLD. Its preserved comparison
  reports1.013xrepresentative workflow,1.001xneural block and1.117xinterleaved
  planner p95speed ratios, not the2x/2x/30%targets. Memory benefits do not replace
  failed runtime targets. No performance code is imported into isolated V1.
- V1:assess only its own frozen gates on the exact isolated source, with original
  scientific claims, independent of optional same-source timing failures.

No neural scientific acquisition, controller retuning, locked cohort access,
merge, tag, publication or broad optimization follows this review.

## Final cross-stage disposition

No new comparative performance acquisition was used to clear a failed gate.
The functional replay harness retains incidental nine-sample measurements, but
these were not selected/re-scored as performance qualification evidence. Existing
M010 banks and every unfavorable sample remain intact. Tiny BLAS introspection
is environment metadata, not a performance trial or actual thread-count proof.

Engineering diagnostic source9fca6f6420d5ddc77c1a7b815913af699544b080 passed hosted
legacy41929355146, package41929355305 and dedicated persistence41929355287. These
are software/diagnostic results, not proof of FIR/RLS tail-latency compliance.
The optional personal-style branch remains HOLD. The V1.1 performance branch
remains HOLD with its failed speedup targets. Independently, the exact isolated
V1 candidate42e20ada6e737c37f616950056c3444cfa99d400 failed macOS clock-fixture
qualification in41929010204 and remains publication HOLD. No new numerical
scientific experiment, target/controller retuning or locked-cohort access occurred.
