# Final macOS CI gate failure — stop decision

Exact tested candidate f79538f18529e21a4a82b6e574e6d0a84822abc3.
Run41788028586:LinuxPASS;macOS198passed,1failed,25warnings,92.34s.
Legacy41788028432PASS. Earlier39400fc4macOS199PASS remains an executed earlier result.
No manual rerun, changed timeout, skipped test or success substitution performed.

Failure:tests/test_supervisor.py::test_real_worker_lifecycle[before].
The fixture uses a1.8s absolute deadline and reserves .8s for cleanup. Its worker attempts
sleep until .2s before the1s work cutoff, then exits. The test requires COMPLETED;
actual returned status DEADLINE_EXCEEDED. Reading partial.txt and the<4s outer elapsed
assertion passed before the failed status assertion. Cleanup/reaping/finished<=deadline
assertions follow the failed assertion and therefore were NOT checked for this case.
Raw returned.json,worker/pid timestamps and supervisor terminal artifacts were not uploaded
by the existing CI workflow. Exact actual completion/cutoff timing and cleanup cannot be
independently reconstructed from available logs.

The production supervisor conservatively treats completion observed after cutoff as failure.
This result is consistent with oversleep,scheduling/import/persistence delay or cutoff race,
but it does NOT establish which occurred, nor prove a supervisor defect or a harmless flake.
Identical source previously passing is not a substitute for explaining this failure.
No evidence here establishes a false successful trial after deadline.

STOP:V1.1 mandatory hosted qualification is FAIL/HOLD. V1 release publication readiness
also HOLD pending this new evidence review because the same supervisor/fixture is shared
with V1, despite its exact release PR checks being green. No scientific result changed.

Smallest next engineering investigation:preserve returned.json,terminal/progress,worker logs,
pid timestamps and outer timing in CI artifacts on every failure; use an independent bounded
watchdog to instrument completion relative to work/global cutoffs. Retain existing thresholds
and outcome assertions during diagnosis. Deterministic injected-clock tests can isolate
boundary logic; they cannot replace real process cleanup qualification. Any fixture-contract
repair must be prospective and justified rather than increasing budgets to get green CI.
No new experiment or code repair executed after this stop decision.
