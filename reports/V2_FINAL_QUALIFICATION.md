# NEUROMANCER V2.0rc1 qualification

The integrated pre-style candidate is the release source. Local
engineering qualification passed. Publication requires the successful
hosted Linux and macOS jobs on the final branch tip and maintainer review.
The style candidate remains on its separate review branch after its
performance gate failed.

## Source and preservation

The base `bf4a74f34f0eab8df528d235d27afecace4916d5` contains all
five required sources in order. The branch audit records their exact
revisions, the unrelated branches, all 38,732 baseline tree entries
as listed in the inventory, and physical source/evidence hashes.
The preserved-path verification checks 38,721 archive, documentation
and Python paths, with explicit review of the active SDK verifier
extension. Historical findings and raw data remain byte-identical.
The final preservation ledger lists every preexisting changed path.

Integrated baseline seal `4ec262486ab953591b90c860dd3515ce531789b7`.
The style implementation is `a9e7ee788cc2036a0a642254fbd00d2298ef110d`
on `refactor/v2-m017-personal-style`, with recorded qualification in
`f5703ce048c30ac4fa050c5b5f9bde3e3b73c296`. Its numerical tests
passed and measured timing failed. The release carries the review
reports and preserves the pre-style runtime.
[Architecture](../docs/ARCHITECTURE_V2.md) ·
[Preservation](engineering/evidence/m017/final_preservation.json) ·
[Style review](engineering/V2_PERSONAL_STYLE_REFACTOR.md)

## Local release checks

| Gate | Result |
|---|---|
| Historical and new public-boundary regression | 228 passed, 46 warnings, 41.96 s pytest |
| Demo A Brian2 control | PASS. Ten network-0 ticks and exact reset replay with synthetic calibration, legal pA, causal PI and receipt-aligned FIR/RLS |
| Demo B neural computation | PASS. M013/M014 summaries independently reproduced from scratch archive copies |
| Demo C CL SDK | PASS. Nine real SDK simulator sessions, 144 bins and 28 matching commitments. PI MAE 1.50 vs frozen 1.00 |
| V1 evidence | Four numerical outputs and four figures byte-identical. Independent model and statistics checks passed |
| M015 preservation | Gate HOLD and retention not run preserved. The reduced three-cell rerun passed all eight cases and exactly matched 56 archived arrays |
| Wheel | PASS. Clean install, imports, dependency check and installed CLI smoke |
| Hardware interlock | Simulator-only execution. Hardware unvalidated. Biological validation not run |
| Style | Exact 102 arrays and deterministic JSON, 228 post-style tests and semantic SDK replay. Planner/PI timing failed |

The 95,561-byte wheel is
`neuromancer-2.0.0rc1-py3-none-any.whl`, MIT, with SHA-256
`a163eb43d8faa7d2578a0eccb8746bbac34fbdfb9efbdf1ccd21a8238041f71c`.
Its 42 entries contain package code and metadata without research
archives. The package now declares the SciPy dependency already pinned
in the core scientific environment. This fixes the older Linux CI
environment that failed to collect the M015 tests. The separate SDK
environment uses CL SDK 1.0.0. Its live process is qualified separately.
[Wheel inventory](engineering/evidence/m017/wheel_inventory.txt) ·
[Reproduce](../docs/V2_QUICKSTART.md)

## Supervised stages and retained failures

| Stage | Wall seconds | Result |
|---|---:|---|
| First baseline probe | 13.058 | Worker failure on strict JSON export of expected PI NaN |
| Completed golden engineering probe | 5.321 | PASS, 102 arrays, 986,169,344 bytes peak worker RSS |
| Full baseline regression | 42.189 | PASS |
| M013/M014 archive verification | 4.796 | PASS |
| V1 archive reproduction | 82.670 | PASS |
| SDK simulator matrix | 5.577 | PASS, 266,387,456 bytes sampled tree RSS |
| Installed CLI smoke | 9.482 | PASS |

The reporting fix put PI state into typed arrays. It did not change
controller behavior or filter samples. Stage supervisor receipts,
logs, measurements and data are archived. SDK recordings occupy
15,272,148 bytes, with verified observed descendant cleanup. No
historically locked cohort was opened. No new scientific study ran.
The one-pair style timings retain unfavorable measurements.
[Performance](V2_PERFORMANCE.md) · [Evidence ledger](V2_EVIDENCE_LEDGER.md)

## Hosted acceptance

Earlier hosted V1 M012 qualification passed. M016's original legacy
Linux failure was SciPy import collection, while its package matrix
passed. On the M017 integration revision, legacy Linux, the SDK
Linux/macOS matrix and the Linux wheel job passed. The exact final
revision requires its own results. Use the branch's Actions checks
or query the commit directly:

```sh
gh run list --commit "$(git rev-parse HEAD)" --json name,headSha,status,conclusion,databaseId
```

Mandatory workflows are substrate qualification, V1 package and
regression qualification, and V2 SDK simulator qualification. All
must finish successfully for publication readiness. No publication
operation is part of this candidate review.
