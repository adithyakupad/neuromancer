# M030 numerical determinism

The diagnostic starts from M029 source `ee2c519d62188dc234d0cce9fb31dd2efe911277` and archived evidence `6295123e7055b4213af11f2c2a3540f02399cf2d`. The original eight-branch comparison has three differing native trajectory hashes and one differing planner cost radius under the ordered verifier. The earlier verifier has one coefficient-radius difference at step 1250 of n1/r47 STATIC.

## Bounded diagnostic protocol

Run the original eight manifest branches once at one worker and once at two workers for each kernel on the same Intel job. Use the existing 180-second component budget and supervisor for each configuration, in ordered-kernel then original-kernel order. No retry is selected from outcomes. Trace n0/r47 LOSS, n1/r47 STATIC and n1/r47 LOSS. Capture raw current history, observations, standardized inputs, all evaluated native matrix products and post-update floating states. Save matching binary64 bits and input addresses modulo 64. Keep each branch's existing chronological certificate, planner comparisons, original candidate bank and exact policies.

An isolated copy of the native update method wraps its matrix multiplication expressions. This preserves the operation tree and changes allocation and timing. The trace can establish an operation divergence in the observed replay. It cannot identify an operation in a prior execution that recorded only a hash. A non-reproduction is retained as such. The step-1250 probe saves original certificate inputs and independently reconstructs the residual magnitude, reduction and outward multiplication. Its attribution is valid only if it reproduces the compiled value bit for bit.

This is a diagnostic run. It cannot pass the original mandatory fingerprint gate or qualify publication. The production package, historical assets, deadlines and approved acceptance rules are unchanged.

## V1 audit protocol

Preserve the exact legacy audit and its failed hosted digest. A small reference witness from the original first update is authenticated by that immutable archive digest. The host replays the identical observed inputs, records the first new state and operator values, and certifies the stored and recomputed states against the shared information recurrence. The exact initial model, feature order and discrete observations remain prerequisites.

The remaining workflow runs all original M029 numerical families under the existing single 240-second deadline, followed inside that deadline by the V1 supplement. Audit 40 fixed and 40 bias-model branches. The bias enclosure starts at the exact archived state, carries gain and intercept uncertainty through every update, and checks the untouched native model and archived forecasts and dense snapshots. The archived scalar policies, candidate scores, selected forecasts and delivered actions receive independent checks. A previously complete, verified RLS matrix can bind fresh per-bin forecast replay to its exact native trajectory hash. Reverify every branch ledger before using it. A complete Intel matrix remains a prerequisite for the Intel RLS supplement. The M029 Intel partial evidence is excluded from this role.

## V1 first archived digest and complete Linux audit

The first failed original model-state digest is bin 0 of n0/r47 STATIC RLS-MPC. The reference host's untouched update produced archived digest `f4e86ea4173a8df51b7b7a9b140f91952c3c1d45440ff32e990e476ebec66757`. The checked-in witness contains those reference state bytes and a separate operand trace. The archived digest authenticates the state bytes. The reference trace also reproduced the untouched update exactly.

The Linux replay had bit-identical initialization, input history, rates, standardized features and centered rates. Its first observed differing arithmetic result was column 3 of `z @ P`. The archived reference value was 0.002796818442113817, bits `0x3f66e95a77bc3d6f`. Linux produced 0.0027968184421138173, bits `0x3f66e95a77bc3d70`. Its separate trace matched the untouched update digest `ab95698392b13c8ea4dd24b6ffdf79f9101bce1f16a2eb7a1eba265fbe32155e`. The exact rational dot rounds to the Linux value. Errors from the exact rational sum were 3.2753e-19 and 1.0615e-19, both within the original gamma(41) bound of 2.2155e-17. Full operand values and bits are retained.

The first new coefficient difference was at (0, 1), `0x3f75182ded281dc7` to `0x3f75182ded281dc8`. The first covariance difference was also at (0, 1), `0xbebe300a7d82d956` to `0xbebe300a7d82d957`. Both states satisfy the residual/inverse proof against the same exact starting information and first observation. These data localize the reference-versus-Linux discrepancy to a native dot product. They do not identify the machine instruction selected by the backend.

The new audit covered 20 saved initial fits, 128,000 fixed states, 128,000 bias updates and 128,000 RLS updates. The fixed model's stored state hashes matched exactly. Linux had 109,091 different bias-state digests. The bias proof propagated its original scalar gain and intercept recurrence with outward rounding, checked every untouched native update, and compared all archived predictions and dense snapshots. Its largest intercept radius was 7.744e-11. For RLS, every M029 Linux branch ledger was reverified and each fresh trajectory reproduced its checked native SHA-256. The reference certificate reproduced all archived digests. The sum of the two original coefficient radii bounds their difference at every step by the triangle inequality. Fresh and archived pre-update predictions passed within the resulting forecast envelopes. No state was restarted from a dense snapshot.

The independent policy audit reproduced all 832,000 exact delivered actions, the original scalar and MPC frames, and all 4,800,000 candidate scores under operation-derived bounds. Candidate banks, fixed objective terms, planner origins and tie outcomes were exact. The largest RLS forecast radius was 2.663e-7. Original M029 fitting, SVD, forecasting and scientific-archive checks also passed. The original strict hosted digest failure remains recorded.

The full local supplement and original remaining stage finished in 128.46 seconds. The final-source Linux run completed in 183.76 seconds under the same single 240-second budget with verified cleanup. [Linux V1 audit](https://github.com/adithyakupad/neuromancer/actions/runs/42550540552).

## Intel operation-level result

The hosted trace used source `bbb67236dd54b79206e96d42924fb45e35447b98`. Each of four configurations completed eight branches under its original 180-second supervisor with verified cleanup. The ordered kernel passed its independent rational residual and alignment/underflow fixtures. Both compiled kernels retain their original operation-derived enclosures and compiler flags. All traced branch proofs kept every chronological update and checked exact archived planner decisions and delivered actions. [Intel first-divergence job](https://github.com/adithyakupad/neuromancer/actions/runs/42549973944).

| Previously affected branch | First observed differing arithmetic | First differing stored update |
| --- | --- | --- |
| n0/r47 LOSS | No difference reproduced in the bounded traces | No difference reproduced |
| n1/r47 STATIC | Bin 1, scalar outer dot `(z @ P) @ z` | Bin 1010, coefficient (0, 2) |
| n1/r47 LOSS | Bin 1, scalar outer dot `(z @ P) @ z` | Bin 2880, coefficient (9, 0) |

Indices are zero-based. At bin 1, both affected branches produced 0.009397059057654287 and 0.009397059057654289 in their one- and two-worker runs. The bit patterns are `0x3f833ec3eaa64f32` and `0x3f833ec3eaa64f33`. The entire previous model state, current observations and both dot operands matched bit for bit. The addition of 0.999 rounded to the same denominator, so that early difference did not reach a stored state.

At the first changed stored states, the outer dot was the only differing input to the original gain and state-update arithmetic. Independently applying those original formulas to each recorded dot product reproduced both complete coefficient and covariance arrays bit for bit.

| Branch and bin | Quadratic bits, 1 → 2 workers | Denominator bits, 1 → 2 workers | First changed coefficient bits |
| --- | --- | --- | --- |
| STATIC 1010 | `0x3f4bf87e496f9e00` → `0x3f4bf87e496f9e01` | `0x3feffeccf8a8e312` → `0x3feffeccf8a8e313` | (0, 2), `0x3f9c32f484b4ef00` → `0x3f9c32f484b4eeff` |
| LOSS 2880 | `0x3f5773fe4b81fc00` → `0x3f5773fe4b81fc01` | `0x3ff001c46c1e2414` → `0x3ff001c46c1e2415` | (9, 0), `0x3fa36ffa7a6eb8a5` → `0x3fa36ffa7a6eb8a6` |

An independent exact rational dot verifies that both rounded results in each row fit the original gamma(41) bound. At bin 1010 the errors were 7.593e-20 and 3.249e-20 against 3.951e-18. At bin 2880 they were 4.721e-20 and 1.696e-19 against 6.516e-18. The shared input and previous-state evidence and exact downstream reconstruction localize the propagated difference to native RLS reduction arithmetic in these instrumented executions. The storage addresses modulo 64 differ. This capture did not isolate alignment, scheduler state or the precise dispatched machine instruction as the trigger. The trace wrapper changes allocation and timing, so it cannot authenticate the missing operands in the original M029 jobs.

The ordered run also had a different native trajectory digest in the untraced n0/r47 STATIC control. Its first operation remains unresolved. The original M028 kernel run had matching component fingerprints and did not reproduce the historical n1/r47 STATIC coefficient-radius difference. At the actual step-1250 plan call, both maxima were 4.0408159195032525e-09. All four calls at update count 1250 matched between worker counts in original input, intermediate residual reduction and reconstructed outward coefficient bound. Each reconstruction matched the compiled output bit for bit. The historical one-ULP radius discrepancy therefore remains unlocalized. Treating a new matching trace as a repair would overstate the evidence.

The runner reported four Intel i7-8700B CPUs, NumPy 2.5.4 with the Accelerate framework, X86_V2 baseline and X86_V3 available. It used Python 3.12.10 on macOS 15 with the original one-thread BLAS environment requests. NumPy did not report an active BLAS thread count. CPU flags, loaded library links, package versions and actual operand addresses are archived. [Ordered operand evidence](evidence/m030_determinism/intel-ordered-operands.json) · [Original radius reconstruction](evidence/m030_determinism/intel-original-first-divergence.json).

The approved numerical proof certified the scientific decisions in every completed Intel component, including both differing native trajectories. The strict worker-count equality gate still fails. It requires a deterministic native execution or an explicitly approved prospective decision on proof equivalence. [Decision record](M030_FINGERPRINT_DECISION.md).

## Intel V1 audit and remaining work

The Intel V1 job at `8794e8d7bdff57bde169b0dfd884f8e6be8a4e76` used the same reference witness. Its first differing product was also `z @ P` in bin 0 of n0/r47 STATIC, this time column 1. The bits were `0x3f66e95a77bc3d6d` in the reference and `0x3f66e95a77bc3d6e` on Intel. Its probe reproduced the untouched update digest. The exact rational errors were 3.5592e-19 and 7.7762e-20 against a 2.2155e-17 bound. Both recomputed states passed the same continuous information residual test. The original exact archive failure remains in the artifact. [Intel V1 audit](https://github.com/adithyakupad/neuromancer/actions/runs/42550540552).

The Intel run passed all 102 golden array obligations and the original fitting, SVD, forecasting, canonical V1 and M013–M016 archive stages. It also verified the first digest and all 20 saved fits. It retained 43 complete model branches, comprising 40 FIXED and 3 BIAS, before `DEADLINE_EXCEEDED` at 239.481 seconds with verified cleanup and no outer watchdog intervention. The remaining 37 BIAS branches, complete policy/plan replay and the 40-branch native RLS linkage are outstanding on Intel. The RLS linkage also requires a full Intel RLS certificate accepted under the worker-count gate. The old 240-second remaining-stage budget remains in force.

Source `92a309ba3398bb6befd467d7660d7e71653cd608` failed the first hosted witness checkout because the repository ignore rule excluded its new NPZ file. The corrected source explicitly tracks that authenticated file. The failed attempt is retained. [Initial witness checkout](https://github.com/adithyakupad/neuromancer/actions/runs/42550521337).
