# Prospective acceptance approval

The maintainer explicitly approved both choices in the conversation after reviewing `FINAL_QUALIFICATION_RESOLUTION.md`.

- Approve the proposed operation-derived portability contract for implementation and fresh qualification.
- Approve A1 phase-specific acceptance for prospective implementation and qualification.

This supersedes the pending-decision paragraphs of the initial report. It does not authorize accepting a failed trial as successful, changing historical data, changing scientific gates, increasing deadlines, or claiming that a proposed error certificate has passed.

## Bounded implementation and qualification

Use a new stdlib-only real worker for running-phase suspend tests, retaining the exact 1.8-second budget and .2/.2/.4-second cleanup policy. Require the injection to occur before work cutoff. A missed setup remains failure. Add a separate cancellation-phase real-process control. Its trial must remain failed and any independent post-result process check must be reported separately. A single narrowly hashed authorization updates the protected active suspend fixture. The historical manifest and former authorized hash are preserved.

Implement outward-rounded interval arithmetic for operation-derived product, residual, RLS and prediction bounds. Require finite enclosures and a strictly positive RLS denominator lower bound. A bound crossing an existing algorithm guard is a qualification failure, even if actual floats are stable. Do not widen a radius limit or reset to archived state to obtain PASS. A fixed 256-update synthetic trajectory checks whether the interval implementation can support the longer archive verifier. If it cannot, retain numerical HOLD and do not run an uncertified full archive verifier.

One local focused run, one full local run and one new exact-source hosted attempt are prescribed. Each host performs three fixed rounds of real running-phase and cancellation-phase checks, stopping on the first failure. The numerical certificate runs once per host under the existing 180-second diagnostic supervisor. Existing core workflows stay enabled. No unqualified contract is used to publish.

The 256-update feasibility trace completed with positive denominator bounds. The next fixed saved-data gate is the first existing primary trial in provenance order, `n0_r47`, branch `STATIC_RLS-MPC`, all 3,200 bins. Propagate uncertainty continuously from its exact archived initialization and check every stored dense snapshot, every candidate score and every selected action. Stop at the first uncertifiable invariant or ambiguous action, retaining the trace. If this branch passes, traverse the remaining RLS branches in original manifest order under the same 240-second absolute stage budget. No per-branch deadline reset, alternative branch selection or bound relaxation is permitted. Full platform qualification remains blocked if this gate fails.

Final code review identified a missing fail-closed precondition for underflow in radius arithmetic. A narrow repair rejects potential underflow and avoids introducing subnormal radii for exact zero bounds. One final source attempt is permitted to verify this correctness repair, retaining all earlier outcomes. The numerical criteria, 256-update prerequisite, 40-branch order, 240-second verification deadline and first-failure stopping rule remain unchanged. There is no retry of an unchanged source to seek a favorable outcome.

A final failure-path review found that the running-phase setup guard could repeatedly raise from the injected clock after setup missed cutoff, interrupting cleanup. The correction latches setup failure while continuing native clock reads, and the test retains a failed setup verdict. Observer-driver failures also receive explicit emergency containment records. This is a narrowly scoped test-fixture correctness repair, not an acceptance relaxation. One final combined source attempt verifies these corrections and the arithmetic-domain guard. All prior failures and source revisions remain retained, and no unchanged failed numerical gate is retried to seek a favorable result.
