# V1.1 optimization ledger

Scientific baseline `abd811a0`; performance-only changes, no new scientific acquisition.
P0 baseline branch `performance/v1-1-baseline` ends at `37f14c32`.

| Stage | Variant | Qualification | Promotion |
|---|---|---|---|
| P1 | SHA256 header then contiguous buffer update, same payload |189 tests PASS; noise/model signatures exact; traced noise allocation480MB to240MB |accept allocation reduction; no material noise runtime claim|
| P2 | explicit out= coarse noise arithmetic |191 tests PASS; exact noise; no additional traced-memory benefit, median0.1348s vs P1 0.1334s |REJECT; restore original expression, retain evidence/tests|
| P3 | stop repeated clipping after every candidate reaches its held command |199 tests PASS; all625 candidate values/scores/actions and original tie cases exact |accept measured bank latency improvement|

No Brian scheduler/GC hooks, backend changes, neural equations, clocks, random draws,
recording memberships, PI behavior, RLS equations, model inputs, planner candidate sets,
objectives or tolerances were changed. No numerical-dependency upgrades.
The complete prediction array still exists for evidence: memory layout/score reduction
order unchanged. No cross-trial mutable caches. Planner250ms timeout checks remain in place.

Original _brian.py and planner are archived in docs/history. The M002.3 test now checks
its unchanged historical hashes against the exact _brian snapshot, with all other
source checks retained. New-source equivalence is a separate test, not a claim of
identical source provenance. The complete baseline tracked-file hash manifest is retained.

P4: one-vs-two-worker fixture measured, no default scheduler change promoted. This small
job bank cannot identify the optimum worker count for large studies. No speculative
oversubscription or BLAS claims. P5 final rerun/evidence reproduction follows this ledger.

All25 warnings are retained Brian2/pyparsing deprecations. No suppressed/skipped tests.
Physical suspend not tested; qualified native continuous clock and bounded process groups
remain the existing resource contract. No hard real-time or hardware qualification.
