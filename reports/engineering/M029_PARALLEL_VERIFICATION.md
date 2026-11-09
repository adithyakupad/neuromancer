# M029 parallel verification protocol

The base is M028 implementation `e2836b355950c62e5dac6f69abee92e2476fe92c` and evidence `e355473f2cfcfa46a449e05f3e0cb905a8714d5c`. The M028 macOS Intel prefix stopped at 29 complete branches and 93,000 updates under the original 240-second limit.

Every branch starts with its trial's saved initial model, covariance and history and reads its own immutable observations, delivered inputs and planner snapshots. M027 creates a fresh model and information certificate inside the branch loop. The archive path consumes no random numbers. The M028 planner query cache depends on immutable normalizers, histories and candidate inputs. Its covariance cache is process-local and checked against the actual covariance object and bytes. Neither cache supplies another branch's initial state. The proposed worker runs one complete unchanged sequential recurrence in a fresh process with fresh caches. Only archive selection and artifact ownership change.

The information and right-hand side intervals advance through `S ← λS + zzᵀ` and `H ← λH + zyᵀ` in each branch's original update order. Each step checks the native approximate inverse through `I - S P` and the coefficient residual `H - S theta`. The inverse bound follows from the Neumann series when the residual norm is below one. Every valid update checks a strictly positive denominator lower bound. Saved states contribute independent residual comparisons at dense checkpoints. They do not initialize the next interval. A worker boundary occurs only at a distinct branch's original initialization.

## Prospective experiment

Run the same first eight manifest branches once per worker count in order 1, 2, 4 on macOS Intel and Linux. Use only counts at most the observed CPU availability, with at least 1 GiB reported host memory per allowed worker and at most four workers. Set the existing one-thread BLAS environment before process startup and record runtime observations separately. Each configuration has one 180-second supervised component budget. This component matrix does not qualify any of the forty-branch stage. Compare each branch's numerical checkpoint fingerprint and counts to the serial worker-count control. A failed configuration, cleanup failure, missing resource evidence or unequal fingerprints stops promotion on that host. Run at most one forty-branch stage per tested source and host with the fastest measured qualified count. Its single 240-second budget includes startup, all branches, cleanup and validated aggregation. A new attempt requires a specific diagnosed defect and a source correction, with all earlier attempts retained. Stop at an unresolved cutoff or numerical failure.

Submit branch commands in original manifest order and aggregate in that same order. Record scheduling and cleanup through the existing supervisor. Retain the original component files, uncommitted tails and terminal records. Record worker CPU and peak RSS, and sample simultaneous process-group RSS once per second. Sampling yields an observed peak lower bound on the true peak and misses short-lived peaks. Timeouts use the existing absolute clock and cleanup reserves with an independent outer watchdog. No supervisor changes are in scope. A watchdog intervention disqualifies the stage.

## Prospective fallback after the Intel fingerprint failure

Source `a6d43e7f24bdd948e029da3cd2a32c1d19d6c91e` stopped at the original strict equality gate. In branch 04 at step 1250, the only recorded scientific checkpoint field that differed between counts 1 and 2 was the coefficient radius, 4.0408159195032525e-09 versus 4.040815919503252e-09. Both supervisors completed. Four workers and the full stage were consequently unexecuted on Intel. The diagnostic cannot identify the responsible operation from those retained values alone.

The one fallback hypothesis is that a fixed summation order for the four-output residual products will eliminate this last-bit proof variation. Compile a separate verification kernel from the preserved M028 source plus a source-bound overlay. Change only the three matrix products in the four-column residual evaluation. Retain the existing rounding model, every original residual and guard, and exact equality of numerical fingerprints. Native model, covariance and planner operations remain unchanged. Test an independent rational oracle and record actual timings for one fixed matrix on each host. Stop on any unresolved mismatch, resource cutoff or proof error. The original experiment remains failed regardless of the outcome of this source change.

## Qualification results

The initial source `7bc21c69b4292d04de488aa3c74fe7d251dcdd6d` stopped because the archive adapter omitted the JSON serializer used by the original driver after writing its terminal certificate. The source correction restores that interface. The initial failures and successful cleanup remain retained. [Initial hosted run](https://github.com/adithyakupad/neuromancer/actions/runs/42537294231).

Source `a6d43e7f24bdd948e029da3cd2a32c1d19d6c91e` qualified every branch locally and on Linux. Intel stopped before the four-worker experiment because of the coefficient-radius fingerprint difference described above. [First corrected hosted run](https://github.com/adithyakupad/neuromancer/actions/runs/42537331495).

The ordered fallback at `ee2c519d62188dc234d0cce9fb31dd2efe911277` still failed on Intel. The original coefficient-radius difference disappeared. The stronger instrumentation also hashed the original native model bytes after each update. Native trajectory hashes differed in three of the eight component branches at counts one and two.

| Branch | Native trajectory bytes | Stored bound difference |
| --- | --- | --- |
| n0/r47 LOSS | Different | None |
| n1/r47 STATIC | Different | None |
| n1/r47 LOSS | Different | Cost radius at step 3050, 8.339018654311824e-09 versus 8.339025863640672e-09 |

All eight branches in both components still independently certified their 3,200 updates, 64 planner decisions, exact archived delivered actions and positive denominators. The differing trajectory hashes identify variation in the native floating-state path across the measured configurations. The retained evidence does not isolate an exact native instruction or prove that worker count caused the variation. The strict predeclared equality decision still fails. The final Intel four-worker component and full stage remain unexecuted. [Ordered hosted run](https://github.com/adithyakupad/neuromancer/actions/runs/42538164882).

The ordered products accumulate four output columns in increasing input index order. With separate binary64 multiplication and addition and no reassociation or contraction, each term contributes through at most the existing dot-product rounding depth. The overlay uses the original gamma and outward-rounding terms for each of the three residual products. A rational oracle independently bounds the signed residual and its input-radius contribution. Alignment and underflow tests preserve the fail-closed arithmetic domain. The overlay is source- and binary-hash bound and remains outside the research wheel.

Every successful stage used its existing supervisor and verified worker-group absence before aggregation. The independently scheduled workers inherited one absolute deadline. Coordinator checks include exact source, kernel, PID, group, clock and deadline identity, worker return status, SHA-256 of each artifact, full ledger chain and no uncommitted tail. The canonical set must contain exactly one successful ledger per manifest branch. Missing, corrupt, foreign or incomplete ledgers fail qualification. Any worker failure prevents stage promotion. The original watchdog and cleanup records are retained with the timed runs.
