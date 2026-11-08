# M009 V1 qualification scope

Base release/v1-license-version c7012fc4, version1.0.0/MIT. Backport only M008 supervisor,
fixture/clock-observation tests and failure-retaining CI. Exact source08a956ce; explicit
file allowlist in backport_manifest.json. Do not bring the performance branch ancestry,
noise digest/coarse-array changes,planner optimizations,performance tests or style changes.

Expected suite183original V1 tests +17M008 tests=200. Preserve historical source/hash checks,
adding only an exact old-CI snapshot lookup. All numerical source besides supervisor remains
byte-identical to V1. Scientific evidence/protocols,dependencies,version and license unchanged.
Local qualification900s shared supervisor budget; pinned existing Python3.12 environment.
Run full suite,pip check,wheel build,installed-wheel smoke,independent process/provenance audit.
Hosted Linux/macOS exact-source CI required. Existing M00835-case diagnostics unchanged.
Any unexpected cleanup/watchdog/causal/numerical failure =>HOLD; preserve failed artifacts.
No full scientific acquisition,locked/validation networks,merge,tag or publication.

Only after qualification create refactor/personal-code-style from this candidate. Style is
not a release prerequisite and must remain a separate reviewable branch.
