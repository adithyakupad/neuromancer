# M008 prospective engineering investigation

Starting ce147866186e8502af343157e4e0d45ac446665a. No neural acquisition or performance optimization.
Scientific source, numerical archives, protocols, controllers and thresholds are immutable.

1. First run20 unchanged original `test_real_worker_lifecycle[before]` cases, sequentially,
   original1.8s deadline/.8s cleanup/6s outer watchdog/<4s assertion. Fresh per-repeat pytest
   basetemp and XML/log. Preserve all failures; no replacement. Additional driver watchdog12s.
2. Add opt-in lifecycle tracing (default production path stays unchanged), instrument worker
   bootstrap, imports, sleep/wake,intent/atexit,parent polling,persistence and cleanup. Trace
   timestamps use qualified same-boot continuous domain. Worker markers are not process exits.
3. Run20 traced unchanged-before cases and3 repeats each of four prespecified perturbations:
   worker wake delay .30s;parent observation stall .30s after a completion marker;
   pre-import delay1.05s;parent progress-persistence delay1.05s. Total32 instrumented cases.
   Perturbations only in fixture code. Expected late observation/work cutoff =>non-success,
   even when a marker was written early. Include3 ordinary immediate-worker controls.
4. Deterministic tests freeze expected outcomes: observed completion well before cutoff PASS;
   exactly at/after cutoff FAIL;intent/exit before but observation after cutoff FAIL;
   after work cutoff before global deadline FAIL;still running FAIL with cleanup;
   TERM/KILL and descendant cleanup required;terminal persistence/clock faults never success.
5. Classify before corrective behavior. If fixture assumption is demonstrated unsound and
   supervisor enforces its contract, preserve original worker and replace the success fixture
   with a verified ready/release/exit handshake with original deadlines and unchanged success,
   elapsed,cleanup and reaping assertions. Keep original race/legacy evidence. Run20 corrected
   repetitions; no timeout increases or success after cutoff. If evidence cannot classify,
   retain HOLD. A specific historical H1/H2/H3 cause may remain unidentifiable without its
   missing logs; do not invent it. Report the general demonstrated mechanism separately.
6. Full focused clock/lifecycle suite, full project suite, independent trace/preservation
   verification, hosted Linux/macOS qualification on final source. Preserve failed records.

Each local batch has a900s suspend-inclusive supervisor deadline, reserve.8s; at most one
trial active, trial commands bounded12s, CPU20s/file-size16MiB limits in diagnostic driver.
At most4 owned test processes simultaneously (pytest,supervisor,worker,descendant).
RSS high-water checked against1GiB for diagnostic drivers; not an OS allocation guarantee.
Full suite has separate900s shared budget, pinned environment unchanged. Hosted existing
20min/15min job limits unchanged. No physical sleep or artificial system load.
No exploratory repetition beyond frozen counts. Any watchdog/cleanup intervention is failure.

H1 sleep overshoot;H2 late parent observation;H3 startup/import/exit/persistence overhead;
H4 incorrect classification of observed timely exit;H5 unjustified scheduling margin;
H6 platform-clock/scheduler discrepancy. Evaluate all, preserving uncertainty.
