# M024 cue-access-first reservoir design

M015 demonstrated structural access and failed its frozen cue-access
gate. Retention remained unrun. Removing E/I edges changes recurrent
feedback, firing rates and cue access together. Reusing the same
held-out outcomes to select a better DAG would compromise inference.

## Stage 1 development calibration

Use fresh IDs 24100–24105. Pair original recurrence, a disjoint-channel
acyclic subgraph, and an acyclic activity-matched sensitivity control.
Keep the recorder layout, signed weights and timing fixed in the
first two arms. Construct the third using a prespecified bounded
baseline current offset fit solely on cue-blind calibration sham data,
with E/I rates reported separately. Report it as a distinct simulator
intervention. Preserve the effective DAG and cue access independent
of the offset. Use independent noise draws across trials and matched
draws across conditions. Pair each cue with sham.

Freeze the cue code and use 20 final cue-window rate features. Use
24 balanced fit and 24 independent balanced development assessment
trials per arm and network, with the same ridge grid and nested
cross-validation within fit. Record rate difference and standardized
evoked response against paired sham. Decode cue only at cue end.
Compute balanced accuracy and the across-network paired cue difference.
Require mean balanced accuracy at least 0.75 in both primary arms,
a paired 90% interval contained in ±0.10 for cue-end accuracy
difference, and stimulus-versus-sham RMS at least twice sham noise
on the fixed recording representation. The activity-matched control
must additionally keep each E/I rate within ±20% of recurrence.
Report every condition and stop before retention when cue encoding
or matching fails.

## Stage 2 conditional delay and distractor assay

Only after cue-access qualification, independently commit a protocol
with fresh cohort IDs starting at 24200, trial counts from network-level
precision, and frozen fit/stimulus/analysis. Randomize delay
20/40/80/160 ms and a distractor presence factor independently of cue.
Primary retention is the paired difference of cue-end-to-probe
accuracy drop at the fixed 80 ms delay. Report the no-distractor
decay curve and prespecified distractor interaction. Compare an
input-history baseline, disconnected diagnostic, and label permutation.
If cue-access matching breaks on the new cohort, report the retention
contrast without attributing it to recurrence.

## Budget and decision

Development proposal only. Before a neural run, use a fresh one-network
bounded cost probe. The prior M015 measured ~0.4 s per trajectory,
so 6 × 3 × 48 cue plus matched sham is an order-of-magnitude 690 s
estimate before overhead. Freeze a 1,200 s cap only if measured cost
fits with 25% headroom. No neural simulation, retention, threshold
tuning or confirmation was executed for M024 in this sprint.
