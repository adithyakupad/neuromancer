# M011 — initial persistence diagnosis

**Bounded diagnostic collection complete locally; hosted results recorded below.**
No production supervisor, clock, durability policy or fixture redesign was made.
M010's incomplete macOS bank remains incomplete; these are new diagnostic trial
identities, not replacements. Optional style and performance gates remain HOLD.

## Historical evidence and question

M010source88218246, macOS package run41902323443, corrected repeat index21:
initial progress-publication envelope954.701138ms; process creation began955.857861ms
and returned960.876689ms; work cutoff999.278845ms; ready1045.387615ms. The creation
call itself took5.019ms, not955ms. Ready missed cutoff46.109ms. The release thread
correctly withheld release, the intended error operation never ran, and the
supervisor returned DEADLINE_EXCEEDED with verified cleanup and no6souter-watchdog
intervention. Three later identities were not launched. Post-bank independent
live-group verification was not run on that aborted case. These limitations are
not relabelled success. Its full artifact and independent timeline remain in M010.

The old trace cannot retrospectively divide that954.701msamong JSON encoding,
file creation/writes, flush, fsync, replace or scheduling. An initial progress
publication envelope is not an fsync measurement. The earlier original uncaught
write-failure episode's exact operation/traceback/shutdown stall is likewise not
recoverable from its incomplete markers. No proven production deadline defect.

## Preregistration and instrumentation

`evidence/m011/PLAN.md` preceded new data. Fixed20cases per host:10ordinary;
2each of1.05swaits before serialization, first write, flush, fsync and replace.
Same original1.8sglobal deadline,1.0swork cutoff,0.2/0.2/0.4scleanup;240sbatch,
6sindependent watchdog,20sCPU/16MiB file ceilings and1GiB measured child-RSScheck.
No physical sleep, load generator or adaptive repeat bank. All outcomes retained.
Controlled holds are artificial waits, not measurements of naturally slow I/O and
not natural failures on isolated V1 source.

Tools:m011_persistence.py,m011_persistence_case.py,m011_verify.py. The fixture-only
atomic_json equivalent keeps the SAME open/write chunks/flush/fsync/close/replace
sequence, JSON encoder/options and file modes. Every initial fsync executes once;
all later production publications delegate to the original function. No fsync is
omitted, mocked or weakened. Production file hashes remain unchanged.

Qualified clock, process CPU and voluntary/involuntary context-switch counters
surround each substep. Per-chunk events remain in memory; a nonblocking stdout
pipe carries stage markers to the independent watchdog process, which retains
partial output on interruption. No diagnostic disk write occurs inside measured
substeps. Full component records are saved afterward; zero dropped markers and
payload/stream correspondence are independently verified. Instrumentation adds
clock/counter/allocation/pipe overhead and is not bit-identical timing behavior.

Python json.dump interleaves encoding and writes. Its full envelope plus each
write-call interval are recorded; subtracting them is not a pure serialization
CPU measurement because observer overhead remains. Buffered writes are distinct
from flush/fsync; fsync wall time includes possible scheduling. Context-switch
counters and wall/CPU gaps cannot uniquely prove a disk-device or hypervisor cause.
Supervisor trace separately captures return to polling, process creation, actual
exit observation, deadline decisions and reaping. Worker ready is not process exit.

## Actual local results

All10ordinary cases executed the genuine failed-publication operation and returned
WORKER_FAILURE. All10controlled holds returned DEADLINE_EXCEEDED, with no worker
operation opportunity. That expected absence is NOT successful execution of an
error control; it demonstrates fail-closed prelaunch budgeting. All20cleanup
records, clock domains, payloads, actual write counts, fsync markers and absent
owned groups passed independent verification. No watchdog intervention or dropped
stage marker. Tables contain ALLten ordinary samples, no exclusion.

| Initial-publication component | Local ordinary median ms | Local ordinary max ms |
| --- | ---: | ---: |
| file_create | 0.055896 | 0.073667 |
| serialization_with_writes | 0.306229 | 0.331875 |
| flush | 0.028854 | 0.040541 |
| fsync | 0.038647 | 0.051250 |
| close | 0.008542 | 0.011959 |
| replace | 0.060396 | 0.075458 |

These fast local observations do not identify the historical955msstage or prove
that it cannot recur on a hosted machine. Raw CPU/context-switch values, all
trial outcomes, manifests and original-clock events remain under persistence_local/.
Independent verification is persistence_local_verification.json.

## Contract interpretation and fixture opportunity

Let W=1.8s−0.8scleanup reserve=1.0swork window. If required prelaunch publication
P plus setupS consumes W, no compliant worker-ready/error opportunity can be
promised before cutoff. OS scheduling and synchronous durability calls have no
measured universal upper bound here. Correct response is a resource failure,
not a retroactive action, a successful error test or a later deadline.

No supervisor violation is shown by rejecting work after that window. A test's
unconditional assumption of prompt publication/readiness is not a proof that the
platform can guarantee it. A reporter/intent marker also does not establish
actual process termination. Blocking synchronous I/O cannot be made hard-real-time
merely by checking a clock before/after; the independent watchdog remains the
outer containment mechanism and all overruns must remain visible.

**No fixture redesign is implemented.** Under unbounded OS/I/O delay there is no
demonstrated universal deterministic opportunity while preserving deadline origin,
mandatory durability and cleanup reserve. Conditional qualification must verify
actual operation and observed exit; missing opportunity remains INCONCLUSIVE/HOLD.
Moving budget start after persistence, removing fsync, accepting absent operation
evidence or silently increasing allowances would change the contract and is rejected.
Separate injected-clock boundary tests may prove conditional logic, but do not
replace real-process/durability tests or prove machine latency bounds.

## Hosted and source separation

The dedicated M011workflow runs the same fixed20cases on Linux/macOS15Intel, then
independently verifies payload/clock/source/probe and same-host group cleanup.
Existing M010engineering workflows remain enabled but their new results do not
replace old failed trial identities or clear performance HOLD. Hosted artifacts,
actual source revisions and results are recorded in the closing appendix.

The observer is confined to engineering/m011-persistence-review. V1's clean release
branch contains NONE of this instrumentation or the failed M010fixture change.
Its own exact-source release gates are evaluated independently. Controlled holds
here are expected negative diagnostics, not evidence of a natural V1 release-test
failure. No scientific/controller code, evidence, gains, constraints, cohorts or
claims changed, and no neural scientific acquisition was run.

## Remaining limits / next action

If no natural stall is observed, retain uncertainty rather than expand the bank.
A future minimal diagnostic may record I/O scheduling/filesystem context for a
naturally slow fsync/publication on its originating host, prospectively bounded,
without changing durability or budgets. Neither a benign rerun nor current fast
fsync values reconstruct the old episode. No optimization or publication follows.

## Hosted closing evidence

Dedicated workflow41929355287, exact engineering source
9fca6f6420d5ddc77c1a7b815913af699544b080: Linux and macOS15Intel PASS.
Both executed the complete fixed20-case bank and same-host independent live
process-group check. Reverification of downloaded artifacts also PASS20/20 per
platform; remote re-verification does not pretend to repeat live remote process
inspection. Logs, ZIP digests and per-case component CPU/wall/context-switch
measurements are retained in evidence/m011/hosted_final. Combined with local,
60/60 planned diagnostic cases completed, no dropped stage records, cleanup or
outer-watchdog failures. This is diagnostic execution PASS, not M010 qualification.

Ordinary-case duration median/max (ms), n=10 per platform:

| Phase | macOS hosted | Linux hosted |
|---|---:|---:|
| create | .148650 / .189093 | .039330 / .077040 |
| encode with writes | 1.667612 / 2.079360 | .422627 / .427567 |
| flush | .174151 / .257223 | .019737 / .042755 |
| fsync | .363007 / .560643 | 2.473480 / 3.228138 |
| close | .050065 / .064691 | .011421 / .047163 |
| replace | .160203 / .206695 | .027986 / .052031 |

Each platform:10ordinary WORKER_FAILURE with deliberate failure operation
executed;10controlled holds DEADLINE_EXCEEDED with no worker opportunity. The
same timings cannot establish an upper OS/fsync bound or locate M010's old
954.701ms publication stall. That old episode remains stage-level unresolved.
Durability, deadline and cleanup allowances are unchanged; instrumentation was
fixture-only and never imported into the isolated release.

Inherited engineering CI41929355146legacy and41929355305package matrix passed on
9fca6f64. Those favorable runs are recorded, not used to overwrite earlier M010
failures or the isolated42e20release failure. On the latter, macOS clock-fault
injection happened before worker imports/checkpoint completed. Source retains
fail-closed CLOCK_FAILURE and verified cleanup; a universal timely partial-file
assertion has not been established. See M011_RELEASE_ISOLATION.md for its precise
separate failure and prospective handshake proposal. No remedy or test weakening
was applied during this mission.

Actual bounded acquisition/verification command entry points:

```text
PYTHONPATH=src /tmp/neuromancer-m007-20261101/bin/python tools/m011_persistence.py reports/engineering/evidence/m011/persistence_local
python tools/m011_verify.py persistence reports/engineering/evidence/m011/persistence_local reports/engineering/evidence/m011/persistence_local_verification.json --live-groups
python tools/m011_persistence.py runs/m011-persistence
python tools/m011_verify.py persistence runs/m011-persistence runs/m011-verification.json --live-groups
```

The last two ran in each hosted matrix job; exact environment, argv, source hashes,
clock identities, budgets and per-case outcomes are committed in their manifests.
Downloaded artifacts were independently rechecked without claiming remote live
inspection. Inherited engineering suites: legacy201passed/25warnings/80.45s;
packageLinux201passed/25warnings/70.18s, macOS201passed/25warnings/216.73s.
These newer optional-branch checks do not replace isolated V1's failed check.
