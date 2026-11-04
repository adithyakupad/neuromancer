# Hosted M010 engineering qualification, frozen before push

Run all201tests in each existing workflow; retain original200without disabling
any and add the late-failure control. Both package-matrix jobs (Linux/macOS15Intel)
and legacy Linux job additionally run the exact fixed25diagnostic conditions
and20timely/5late fixture repeats. Each batch retains its own preregistered240s
limit and6souter watchdog; individual budgets remain1.8swith1.0swork cutoff.
Existing15/20min workflow limits unchanged. No rerun-until-green. Preserve every
trial, including descriptive original-worker DEADLINE_EXCEEDED outcomes. On any
watchdog, cleanup, status or assertion failure stop qualification, retain HOLD.
Upload these outputs even if a later assertion fails. No host-scientific data
acquisition, parameter adjustment or locked cohort use. The hosted probe source
hashes/commit and actual platform labels must be recorded; local Apple Silicon
and hosted Intel macOS are distinct evidence. Original diagnostics are prior-art
cases, not expected-timely-success scientific trials.
