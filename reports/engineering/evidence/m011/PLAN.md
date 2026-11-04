# M011 prospective separation and diagnostic plan

Before new trials,2026-11-04. Engineering base4a8e91ee16ed2458c8978783f251bf045e7dbfa5;
release source86ad99f6956c76a5bb6d169e21544684f57c9270. Two review branches:
engineering/m011-persistence-review and release/m011-v1-isolated. Never import
M010 or optional style/performance production changes into release. No merge/tag/
publication. Local main's extra documentation commit is retained, not reset.

A/D: audit every branch/ref, license/version, ancestry and production/evidence
hashes. Clean pinned Python3.12 environment; build/install noneditable release
wheel, pip check, imported file hashes and installed CLI smoke. Full200-test
release suite; exact91-array original V1 golden fixture (including1s development
neural replay, not a research acquisition); committed-data-only tables/figures
reproduction. Ten preregistered additional original write_failure pytest invocations
on isolated V1 source, no injections, all retained. A natural failure of an
unchanged release test independently establishes V1 HOLD; later passes cannot
rescue it. Frozen release gates remain unchanged: do NOT apply M010's optional
25-repeat bank or FIR/RLS p95gate to V1. All isolated release code checks and
Linux/macOS CI must pass on its exact final revision.1200s local qualification,
240s original-test diagnostic bank,1.8sworker deadline/1.0swork cutoff and existing
cleanup allowances/outer watchdog unchanged. No original scientific acquisition
or locked cohort access. Stop on unsafe cleanup or lost clock integrity; retain
all incomplete attempts. Routine independent read-only checks may still complete.

B: leave production atomic_json/supervisor/clocks byte-identical. Use fixture-only
instrumented equivalent of atomic_json with SAME JSON/options, open/write/flush,
fsync and replace sequence; record qualified clock, process CPU and context-switch
counters in MEMORY around serialization, creation, buffered writes, flush, fsync,
replace and return. No diagnostic disk writes inside timed substeps. Supervise
tracing records scheduling/polls, launch/readiness. Observer overhead disclosed.
20fixed cases sequential:10ordinary,2each serialization/write/flush/fsync/replace
with1.05scontrolled pre-step delay on INITIAL progress publication only. Every
fsync still executes; no omission/relaxed durability. Original1.8/.8reserved
budget and6souter watchdog, CPU20s/file16MiB limits;240s batch,<=1GiB measured
child RSS. All cases retained, ordinary outcomes descriptive WORKER_FAILURE or
DEADLINE_EXCEEDED, held cases must fail closed. These intentional delays are NOT
natural release failures. No arbitrary scheduler or I/O bound is assumed.
A missing operation opportunity is INCONCLUSIVE for error-path qualification,
never successful execution. No new fixture redesign without independently
justified preservation of deadline origin and fail-closed semantics.

Run the same20-case engineering diagnostics on Linux/macOS via a dedicated bounded
workflow, retain every artifact even on failure. Existing engineering workflows
remain unmodified and their outcomes do not transfer across release branches.

C: no new timing benchmark or optimization. Analyze ALL previously committed
M01054samples/source/workload/bank and12process origins, CPU versus wall,
first-measured versus later samples, ABBA ordering, peak RSS and known17.897soverlap.
Bootstrap process-level/cycle-level uncertainty descriptively (not neural units),
fixed seed20261111,10000draws, no sample exclusions. Assess lack of historical
system-load/thread/affinity observations explicitly. Two tiny current NumPy/BLAS
metadata/import probes (original/default and requested1thread env), not latency
measurements and not retrospective thread proof. Produce future protocol proposal
only; do not replace failed gates or run retries toward green.

No production modifications, no perf candidate speedup claims, no threshold
changes. Final independent readiness decisions:V1,style,V1.1 separately. Historic
HOLD/FAIL decisions remain. Commit documentation/evidence only to review branches.
