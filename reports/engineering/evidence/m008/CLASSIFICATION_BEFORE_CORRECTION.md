# Prospective correction decision, after fixed baseline/diagnostic acquisition

Original unchanged20/20 completed locally. Instrumented ordinary20/20 and immediate3/3
completed. Every one of12 controlled delay cases returned DEADLINE_EXCEEDED with verified
cleanup. Ordinary observed-exit margins162.425–189.841ms, median182.502ms; original nominal
margin200ms is reduced by wake overshoot,exit/observation and persistence overhead.
The four delay conditions crossed the work cutoff without changing any deadline.

Classification:Case B, fixture timing assumption defect (H5), demonstrated by controlled
H1/H2/H3 mechanisms and strict documented fail-closed contract. No supervisor decision
repair is justified by these measurements. H4 requires deterministic boundary qualification.
The original success fixture waits until near cutoff then assumes the remaining200ms bounds
all OS/Python/persistence scheduling. Python time.sleep expressly permits arbitrary extra
scheduling delay; Popen.poll observes/reaps termination rather than reporting its exact time.
Neither gives that upper bound. This assertion can fail correctly when resources are late.

Historical exact attribution remains unknown because original timestamps were not retained.
The controlled experiments reproduce the failure class; they do not retroactively determine
whether the actual historical cause was oversleep,late observation,import or persistence.
No H6 native clock fault was observed; macOS-specific scheduling causality remains unproved.

Permitted fixture-only correction:retain the original before worker/archive and separate
race test. Replace the before-success worker with a lightweight stdlib-only clock bootstrap
and explicit ready/release/completion handshake, with immediate exit after release, no
sleep-until-cutoff and no eager NumPy/package import. Original1.8s/.8s/6s/<4s budgets and
COMPLETED/cleanup/reaping assertions remain unchanged. Add assertions that actual parent
observed exit and group reaping precede cutoff; a ready/completion marker cannot qualify it.
Twenty corrected repetitions remain fixed as preregistered. No production timer or success
criterion changes. Continue only through engineering qualification, no scientific acquisition.

Primary documentation accessed2026-11-04:
https://docs.python.org/3.12/library/time.html#time.sleep
https://docs.python.org/3.12/library/subprocess.html#subprocess.Popen.poll
