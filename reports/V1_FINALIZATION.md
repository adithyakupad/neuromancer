# V1 finalization — 2026-11-04

Release-preparation source: `abd811a053e10ad7ee5126efbc95fefd73e55c8d`.
PR #1 remains OPEN/MERGEABLE, base main `011c3ce1a71960544032717e91076730416c19fd`.
No merge, tag or release performed. Publication is READY FOR FINAL MAINTAINER AUTHORIZATION,
conditional on successful checks on this documentation-only PR update.

## Exact source checks

MIT LICENSE contains Copyright (c)2026 NEUROMANCER contributors and the standard
permission/notice/disclaimer. Wheel metadata has License-Expression MIT and embeds LICENSE.
Owned Python code is distributed under MIT; third-party packages retain their licenses.
The small wheel contains own package code/metadata, not vendored dependencies or research
archives. This repository review cannot independently establish every contributor's chain of
copyright title, nor relicense external research material cited in historical source audits.
External linked code/data remain subject to their original rights.

Version1.0.0 is consistent in pyproject, wheel metadata and documented wheel commands.
No scientific src, dependency pins, frozen protocols, numerical reports or evidence changed
between the audited `a504c0c7` and release-preparation `abd811a0`.
Historical metadata is checked against an exact archived snapshot, with unchanged historical digest.

Hosted checks on exact abd811a0: V1 Linux/macOS and legacy suite SUCCESS.
[Release-preparation matrix](https://github.com/adithyakupad/neuromancer/actions/runs/41784163750).
Final docs-only CI must be checked again before publication.

Rebuilt wheel: neuromancer-1.0.0-py3-none-any.whl,83611bytes,
SHA256 `809253b5676b3e3b76181cf50db811716e515a53ba89b548e71a4fb9d071c86f`.
Built with pinned Python3.12/setuptools84.0.0 using pip wheel --no-deps --no-build-isolation.
35 entries;29 source modules; no raw archives. Wheel ZIP timestamps can change its hash
between builds; verify a published artifact against its own supplied digest.
Dependency consistency passed. Full fresh local source regression recorded separately in
performance/evidence/release_tests.xml on the performance review branch; not substituted
for exact-release hosted qualification.

## Scientific scope remains frozen

PI11.46875, RLS13.12921875, fixed MPC18.9778125 Hz*s. Adaptive-superiority FAIL.
All historical V0/M003/M004/M005A failures and qualified findings remain unchanged.
Validation/locked controller cohorts NOT EXECUTED. No biological, plasticity, living-neuron,
hardware-safe or hard-real-time claim. See M007 and V1_SCIENTIFIC_LIMITATIONS.

Git object store ~742MiB, evidence ~1.2GiB measured locally. This is a large research checkout;
wheel83.6KiB intentionally omits archives. Do not migrate/delete historical data to shrink it.

## Concrete publication actions pending authorization

1. Review PR #1 final diff/checks; merge preserving research ancestry (avoid squashing away provenance).
2. On the verified resulting main commit, build/test the wheel and record its source and digest.
3. Create an annotated immutable v1.0.0 tag on that exact main commit.
4. Publish the GitHub release with docs/V1_RELEASE_NOTES.md, wheel and checksum/source manifest.

No authorization for these publication mutations is inferred from routine engineering authorization.
Performance changes live on separate branches and must not be included in v1.0.0.

## Later engineering stop —2026-11-04

The final V1.1 review commit f79538f1 failed macOS run41788028586:198passed,1failed.
The unchanged shared supervisor before-cutoff fixture returned DEADLINE_EXCEEDED instead
of COMPLETED. Exact V1 PR7d63b1f5CI remains green; its earlier outcome is not rewritten.
Nevertheless current V1 publication readiness is HOLD pending bounded diagnosis of the
shared timing contract. No code,deadline,test expectation or scientific result changed.
No manual rerun or publication performed. Failure logs/design diagnosis live on the separate
performance review branch. Final authorization is premature until this gate is resolved.
