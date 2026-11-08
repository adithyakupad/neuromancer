# Final core-release supervisor timing fixture qualification

**Status: review candidate, no altered production timeout.**

A macOS Intel hosted core regression at run [42334001244](https://github.com/adithyakupad/neuromancer/actions/runs/42334001244) failed in `test_real_workers_after_injected_resume[expired_suspend_descendant]`. The test attempted to assert `worker/partial.txt` existed, but it had not been published by the worker at observation time. A different complete core run on the same release revision passed.

## Hypothesis and targeted correction

The fixture previously triggered injected clock discontinuity after 350 ms measured from the test supervisor's start **without** requiring the synthetic worker and its nested descendant to have reached the checkpoint that the test was designed to evaluate. The observed failure is consistent with that setup race; it does not prove the race is the only possible explanation.

The revised fixture retains the original elapsed threshold and injected clock values, but permits suspend injection only if:
- `worker/partial.txt` exists, for all non-clock-failure injected suspend variants;
- for `expired_suspend_descendant`, `worker/child/partial.txt` also exists.

The existing six-second outer watchdog, status/cleanup assertions, original monotonic deadline and all worker signal handling remain unchanged. Failure to reach readiness within the original workload bound still fails, rather than being interpreted as a successful resume/cleanup test. The separate pre-ready and post-ready clock-failure fixtures remain unchanged.

## Exact-file historical authorization

The original M017 protected manifest is **unchanged**. The original `tests/test_suspend_clock.py` digest is `e6ac4422f251c6de7602321c7cc4dc01bffd19a00ff76f8f0e7bcb1bd46eca86`.
The sole newly authorized active digest is `f78dac7ee7caea0f66bd2d573e648933e765b654c6178a90b2778a7debce5bb0`.

This replaces **one** protected file hash under the exact-file authorization mechanism; no path-wide exemptions, other fixture changes, simulation algorithms, production supervisors, SDK interfaces, scientific archives or global CI deadline increases are permitted. The prior M026 three file authorizations remain unchanged.

## Qualification gates before merge

- Run the modified clock/supervisor tests and full regressions on Linux and macOS Intel on the exact final commit.
- Ensure provenance verification returns the same **38,721** historical paths and rejects unexpected edits to every protected path.
- Retain a trace of the previously failing test condition in hosted CI; a passing rerun alone does not identify every possible scheduling issue.
- Preserve the independent macOS accelerated CL SDK producer-stall HOLD. The engineering release scope is **core-only**, and SDK tests are still run and their failures disclosed.
- Do not merge, tag or publish until acceptance evidence has been reviewed.
