# M015 causal memory protocol

Base `9cde9c24d0e2db4c76d70741b4427c1d77962453`. M014 found an
inconclusive positive point estimate against a disconnected control. Its
disjoint stimulation and recording memberships make that control blind to
the cue. M015 separates structural access, measured cue encoding and memory.

## Conditions and graph

C0 is the frozen 1,000-cell Brian2 engine. C1 disables both synaptic
populations. C2 uses the original realization and assigns each neuron to
one of four ordered layers: stimulated E, other unrecorded E, unrecorded I,
recorded E/I. Keep an original edge only if its destination has a strictly
higher layer. Stimulated cells are sources, recorders are sinks. Retained
edges preserve sign, current increment and delay. Zero-weight Brian
placeholders transmit no current. Audit the effective graph from actual
synapse arrays, not just the construction mask. Record SCCs, shortest
paths from all four input channels, edge counts by E/I and graph hashes.
Require all 100 recorders reachable from each stimulus channel in C2.
Preserve neuron parameters, stimulation and recording membership, solver,
100-us step, 20-ms observations and original physical limits. The DAG has
different degree, feedback, inhibitory drive and activity distributions.
No weight scaling, firing-rate clamp or activity-matching intervention.

## Cue access gate

Use development networks 15000 and 15001, root 20261106. Reset original
state each trial and replace only the role-4 OU replicate key. Pair
initialization and innovations across conditions and sham. Use the M014
cue pulse [30,60,30,0] pA on channel 0 or 1, no distractor, and only the
last 40 ms of the completed 80-ms cue for 20 recorded channel rates.
Fit/validation/test counts 16/8/16 per condition and network, balanced
cue classes via the existing M014 factorial scheduler with task ID equal
to network ID. OU replicate key 150000 + 100*split_index + trial_index.
For each of the 16 held-out cue trials also run an all-zero sham on its
identical noise replicate and reset. All exposed and sham trials preserved.

Use M014 fit-only standardization and ridge [0.1,1,10], validation
balanced accuracy, first tie, threshold 0.5. Held-out cue labels only
score frozen predictions. In each network require all of the following:
C1 sham and cue counts exactly identical, C0 and C2 cue-end accuracy
at least 11/16, C0/C2 accuracy gap no more than 2/16, C0 and C2
class-specific RMS across channels of the mean paired cue-minus-sham
vector at least 1 Hz for both cue classes, and C2/C0 pooled recorded
cue-window mean rate between 2/3 and 1.5. Require finite activity and
mean recorded trial rate no greater than 100 Hz. These pilot thresholds
screen for observable encoding and gross activity imbalance. They do
not prove equivalence of cue information or activity distributions.
Require both networks to pass. On failure, retain all results, keep
memory on HOLD and report final accuracy and retention as NOT RUN.
No outcome-informed reconstruction or network exclusions.

## Conditional retention pilot and confirmation

Only on joint cue gate PASS, use the same two networks and distinct OU
replicates 151000 + 1000*delay_index + 100*split_index + trial_index.
Use the original M014 two pulses with independently balanced distractor,
both silent delays 20,80,160 ms. Fit/validation/test 16/8/16 per delay
per condition. Use delay_index+1 for task generator key to separate
it from access. Fit independent probes at cue end, distractor end and
final 40 ms, 20 rates each. Archive accuracy by distractor class,
class-specific rates, covariance/rank and participation ratio. Primary
80-ms final balanced accuracy C0 minus C2 across paired networks.
Meaningful effect +5 pp and two-sided Student-t 95% paired CI lower
bound above zero. Report cue-to-final drop within each condition and
the change in C0–C2 difference between cue and final, descriptive.
n=2 is a pilot regardless of arithmetic. Unopened confirmation IDs
15100–15163, 64/32/128 fit/validation/test per cell, planning SD 20 pp
gives approximately 5 pp CI half-width with 64 networks. Confirmation
requires a fresh resource and design review, with a 3600-s planning cap.

## Resources and stops

Benchmark one original development network 15000, three independent
360-ms D80 trials (OU IDs 159000–159002) with no scoring. Fixed 120-s
benchmark, 180-s regression and 420-s access deadlines. Access 336
trajectories, 26.88 simulated seconds. Conditional retention 720
trajectories, 278.4 simulated seconds (40*6*(.24+.36+.52) = 268.8 s,
the explicit schedule sum 268.8 s controls). Separate 1100-s deadline.
Require 2*(6*construction + number_of_trajectories*maximum_benchmark_trial)
+30 s within each cap. Expect under 2 GiB peak per worker, dominated by
the original 1-s noise buffers. Cap 2 GiB measured RSS and 100 MiB output
per stage. Estimate access archive under 10 MiB and retention under
30 MiB from fixed 20-channel arrays and trial counts. Check at split
boundaries and preserve completed units. Use the existing suspend-inclusive
supervisor and independent watchdog. No deadline extensions.

## Independent reduced simulator benchmark

After causal engineering and access evaluation, compare Brian2 2.10.1
against a standalone scalar Python time-stepping reference with no Brian
calls. This is a new independent implementation, not NEST or a full
replication of the memory network. Three LIF cells, tau_m=20 ms, C=200 pF,
rest/reset=-65 mV, threshold=-50 mV, refractory=2 ms, dt=0.1 ms.
Initial V=-65 mV, zero synaptic currents, constant 170 pA background.
dV/dt=(rest-V)/tau_m+(I_E+I_I+I_drive)/C, I_E/I_I exponential decay
with 5/10 ms time constants. Edges 0→1 +120 pA at 1 ms, 0→2 +70 pA
at 1.5 ms, 1→2 -90 pA at 2 ms. At each step, freeze currents for the
exact membrane leak update, decay currents, threshold, deliver due
events, reset. A delivery affects the next membrane step. Use half-open
20-ms observation bins. Cell 0 stimulus +100 pA at [40,100) ms and
paired sham. Reduced fixture bypasses V1 actuator slew and is not
the memory intervention. Simulate 200 ms. Deterministic drive then
three stochastic cases with shared explicit 5-ms OU, 25 pA stationary
SD, zero initial noise, PCG64 seeds 15500–15502. Same external drive
arrays on both engines, no internal RNG. No cross-simulator spike
identity requirement for larger models.

Qualification: per-cell mean firing rate difference ≤ 0.1 Hz, identical
20-ms population counts, equal ISI sample sizes with max sorted ISI
difference ≤ 0.1 ms (integer ticks), evoked count contrast equal and
current trace absolute difference ≤ 1e-8 pA. Test analytic no-synapse
first spike and arrival indexing separately. Compare decay and binned
covariance descriptively. Reduced verification only, no memory decoding
replication. 120-s supervised cap. Preserve matched inputs, outputs,
and negative results. If unqualified, report the exact blocker.
