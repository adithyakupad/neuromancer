# M030 final qualification

**NEUROMANCER V2 CORE RELEASE HOLD**

The Intel replay localized the first changed stored RLS states in two affected trajectories to one-ULP differences in the native `(z @ P) @ z` reduction. The operands were bit-identical, and independent reconstruction reproduced both updates. The differences satisfy the approved operation-derived bounds. The unchanged mandatory worker-count equality gate still fails. [Numerical findings and exact bits](M030_NUMERICAL_DETERMINISM.md).

| Scope | Verdict |
| --- | --- |
| Independent ordered-kernel oracle and executed Intel branch proofs | PASS |
| Strict Intel worker-count fingerprint | FAIL |
| Complete V1 portability | PASS on reference arm64 and hosted Linux. HOLD on Intel |
| Fitting, SVD, golden outputs and saved scientific archives | PASS on both hosted platforms |
| Core regression | PASS, 307 tests per hosted platform with zero failures, errors or skips |
| Cleanup | PASS for the executed local A1 and supervised runs |
| Historical preservation | PASS, 38,721 protected paths |
| Review wheel and installed CLI | PASS |
| Core release | HOLD |
| Full SDK reliability and personal style | HOLD |
| Biological validation and physical hardware execution | NOT RUN / NONE |

## Scope and provenance

| Item | SHA |
| --- | --- |
| M029 source | `ee2c519d62188dc234d0cce9fb31dd2efe911277` |
| M029 evidence | `6295123e7055b4213af11f2c2a3540f02399cf2d` |
| M030 Intel diagnostic source | `bbb67236dd54b79206e96d42924fb45e35447b98` |
| M030 final V1 audit and core source | `8794e8d7bdff57bde169b0dfd884f8e6be8a4e76` |
| M030 archived evidence | `41f01dd84ba5a73b7daee75ea280ed906257e677` |

The protected manifest SHA-256 is `f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1`. Production code, scientific artifacts and dependency pins match M029. The original strict digest results are retained separately from the new operation-derived comparisons.

The local three-round A1 confirmation passed all 18 checks. Both hosted ordered diagnostic components and the original-kernel components verified cleanup. The Intel V1 cutoff retained its failure and partial proof with verified cleanup. The final hosted release-specific three-round A1 confirmation requires numerical qualification first.

The fresh review wheel is `neuromancer-2.0.0rc1-py3-none-any.whl`, SHA-256 `8d3c841669aa51e233967a876479597c38a09355ff9895650e06af6373032eae`. Its 36 packaged modules and MIT license match the source. Fresh pinned installation, pip check, installed imports and the CLI smoke outside the checkout passed. The verifier extension and evidence are outside the wheel.

## Hosted runs

- [Intel operation traces and independent oracle, 42549973944](https://github.com/adithyakupad/neuromancer/actions/runs/42549973944)
- [Linux complete V1 and Intel deadline failure, 42550540552](https://github.com/adithyakupad/neuromancer/actions/runs/42550540552)
- [Initial V1 checkout failure, 42550521337](https://github.com/adithyakupad/neuromancer/actions/runs/42550521337)
- [Exact final V1/core implementation regressions, 42550540502](https://github.com/adithyakupad/neuromancer/actions/runs/42550540502)
- [Exact final implementation substrate, 42550540474](https://github.com/adithyakupad/neuromancer/actions/runs/42550540474)

## Remaining qualification

The original n0/r47 LOSS divergence and historical step-1250 theta radius difference did not recur under tracing. The observed untraced n0/r47 STATIC control also differed in native trajectory bytes, so its first operation remains unknown. The controlled traces localize the two reproduced differences to native RLS dot arithmetic and leave the backend trigger unresolved. [Prospective fingerprint decision](M030_FINGERPRINT_DECISION.md).

Complete a qualifying 40-branch stage on each hosted platform under the original 240-second cap after the strict Intel equality requirement is satisfied or a prospective replacement is approved. The completed M029 Linux proof was independently revalidated and rebound to fresh M030 native trajectories for the V1 audit. This is separate evidence from a fresh final release-stage matrix. Intel additionally requires the remaining 37 BIAS branch proofs, the complete exact policy and candidate replay, and the RLS forecast linkage to its qualified native matrix under the same original remaining-stage budget.

The scientific findings retain their original scope. V1 adaptive MPC superiority remains FAIL. M013 and M014 remain INCONCLUSIVE. M015 cue access remains FAIL and retention remains NOT RUN. M016 PI improvement remains FAIL. Main and the public release were left in HOLD.
