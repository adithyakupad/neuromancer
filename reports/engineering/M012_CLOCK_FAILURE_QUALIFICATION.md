# M012 — Clock-failure fixture qualification

**Scope:** Isolated NEUROMANCER V1 release candidate, simulation-only. No merge, tag, publication or scientific acquisition.

## Source and change

Starting immutable V1 candidate: `42e20ada6e737c37f616950056c3444cfa99d400`.
Working branch: `release/m012-clock-qualification`.

Only `tests/test_suspend_clock.py` was edited in the qualified source. No production supervisor, clock, neural model, predictor, controller, stimulation constraint, frozen experiment, numerical archive or scientific report was changed.

The historical test expected a worker checkpoint even though its fixed-time clock-failure injection could occur before worker startup. M012 adds two explicit scenarios:

- `clock_failure_pre_ready`: fault during supervisor setup after initial progress persistence but before worker creation/readiness. Assert fail-closed `CLOCK_FAILURE`, no invented checkpoint/readiness and verified cleanup.
- `clock_failure`: launch the existing lightweight handshake worker. Clock failure is injected only when its real `ready.json` and `partial.txt` exist, and before the original deadline. Require fail-closed status, preserved checkpoint, owned-process cleanup and reaping.

The other simulated-suspend cases and the original 1.8-second global deadline, 0.8-second cleanup reservation, escalation policy and outer watchdog remain unchanged. The post-ready mode will still fail qualification if readiness is not reached in time; no later injection is treated as success.

## Executed hosted qualification

Qualified test-source revision: `724eec11dc2fdfff71b64705d115e7d92b22a3e5`.

- [V1 Linux/macOS package qualification](https://github.com/adithyakupad/neuromancer/actions/runs/41947293931): PASS. Linux **201 passed / 25 warnings** in 100.47 s; macOS Intel **201 passed / 25 warnings** in 168.38 s. Both completed the full workflow, including subsequent package qualification steps.
- [Legacy substrate qualification](https://github.com/adithyakupad/neuromancer/actions/runs/41947294001): PASS.

Hosted verification is specific to these revisions and runners; physical sleep/resume, every possible scheduling stall, and full scientific reacquisition were not tested.

## Scientific preservation and release decision

The narrow two-commit change is confined to a clock-injection test. All archived in silico research findings remain in their historical scope: M005B development IAE PI 11.46875 Hz·s, RLS-MPC 13.12921875 Hz·s and fixed MPC 18.9778125 Hz·s. Adaptive superiority over PI FAIL remains unchanged. Validation/locked networks remain unopened.

**M012 hosted software qualification: PASS on the qualified source.**

**V1 publication state: NOT PUBLISHED.** This report is a documentation-only closing commit. Its source/test/workflow bytes are unchanged from the successful CI revision; the new final Git revision should receive independent final-head checks before merge. V1.1 performance and optional personal-style refactor remain separate HOLD tracks.

No local Mac tests are claimed; the qualification cited above was performed by hosted CI.
