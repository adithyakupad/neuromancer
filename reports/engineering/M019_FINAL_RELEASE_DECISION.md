# M019 final release decision

**V2 publication HOLD. M019 producer-boundary investigation PARTIAL.**
The bounded diagnostic reproduced a macOS Intel accelerated SDK
frame wait with a published request and a stationary write head.
It narrowed the failure to the interval after request publication
and before the next producer source callback. The required
producer-side request load or scheduler event remains unobserved.
No production repair met the evidence gate.

- Release candidate remains `70e976c1e990db2fbbc88f786b5d7c06a691aa70`
  on `release/v2-0-research-candidate`.
- Investigation source is `6cd482ca4afb4a807ac1d7471cc85c8a9523c74f`
  on `engineering/m019-producer-boundary`, based on M018 archive
  `8194810b22f6be73a31d647f4375fd118471d829`.
- The hosted diagnostic failed on both platforms. Linux failed an
  HDF5 recording extent check after receiving all requested frames.
  macOS Intel had a frame timeout and two HDF5 extent failures. Every
  worker recorded verified cleanup. The failures remain evidence.
- No integration revision, tag, merge or publication was made.
  Historical numerical evidence, scientific algorithms, models,
  controllers and deadline implementations remain unchanged.
  Biological validation remains NOT RUN. Hardware execution is NONE.

The unchanged release source retains its M018 package, archive and
core checks. The M019 diagnostic job did not qualify an SDK release
revision. Fresh post-repair package and scientific qualification
were not triggered because no repair was made. A passing replay or
another passing SDK job would leave the identified reliability gap
open. Upstream instrumentation at the producer load is the next
discriminating step. The frozen local and hosted execution budget is
closed.

[M019 evidence and interpretation](M019_PRODUCER_BOUNDARY.md) ·
[Preserved M018 release qualification](M018_RELEASE_READINESS.md) ·
[Exact diagnostic CI](https://github.com/adithyakupad/neuromancer/actions/runs/42183363096)

## Exact diagnostic-head hosted checks

| Workflow | Linux | macOS Intel |
|---|---|---|
| M019 SDK diagnostic | FAIL, recording extent | FAIL, frame timeout and recording extent |
| Core package, pytest, supervisor repeats and installed CLI | PASS, 231 tests | PASS, 231 tests |
| Substrate qualification | PASS | No macOS job in this workflow |

The tables and raw artifacts are archived on the diagnostic branch.
The closing report commit did not dispatch another diagnostic or
modify the release source.
[Core hosted checks](https://github.com/adithyakupad/neuromancer/actions/runs/42183363112) ·
[Substrate hosted check](https://github.com/adithyakupad/neuromancer/actions/runs/42183363111)
