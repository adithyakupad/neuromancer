# Prospective repair decision after25fixed probes

Case D: the fixture's inference from an unhandled publication exception to prompt
process exit is not justified. The historical process remained observed running
past cutoff and required TERM; no timely exit was misclassified. Production
supervisor and clocks stay byte-identical. No evidence supports C or E in that
trace. Its incomplete traceback locates it in/after exception propagation, but
missing phase timestamps cannot uniquely distinguish original A/B or an OS stall.
We do not claim the synthetic delay identifies that historical OS subcause.

Executed bank: five original and five instrumented filesystem errors, three pure
Python errors and three explicit failure exits all WORKER_FAILURE; three normal
exit controls COMPLETED. Two each of delayed operation, traceback and shutdown
were DEADLINE_EXCEEDED with verified cleanup. This causally demonstrates that
failure-event creation/display/shutdown and actual process exit are separate
stages: the old unconditional status expectation conflates them. Passing old
repeats alone would not justify repair; delayed stage controls and the original
running polls establish the defective timing assumption.

Retain oldworker unchanged. New fixture gets ready/release under the original
already-created1.8sdeadline, deliberately writes below an existing file, catches
and validates ENOTDIR/NotADirectoryError, records the failure and scientific_
success=false, then exits23 explicitly. The ready/exception/record/exit intent
are evidence only; supervisor-observed nonzero exit and reaping before cutoff
remain mandatory. os._exit is confined to a trusted synthetic fixture, not a
production-worker shutdown recommendation. Files are closed before exit.

A new late-failure condition performs and records the SAME real filesystem error,
then waits within a bounded original absolute deadline, ignoring cooperative
stop but not TERM. Its result must remain DEADLINE_EXCEEDED and never scientific
success, even with a timely failure report. No timeout/grace/status assertion is
relaxed. General unhandled exception, interpreter exit, descendant and cancellation
cases remain enabled. Corrected20timely/5late qualification bank was preregistered.
