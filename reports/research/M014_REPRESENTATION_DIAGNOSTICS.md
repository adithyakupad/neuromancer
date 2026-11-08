# M014 representation diagnostics — methods and interpretation

All diagnostics are explanatory, not independent scientific-success gates.
The primary hypothesis remains final-window D80cue recall, recurrent minus fully
recurrence-disabled network. No plasticity or activity matching is performed.

## Recorded interface

20virtual channels ×5neurons:four excitatory channels and one inhibitory channel
per sector. Final40ms features sum two20mscount bins and divide by5*.04seconds:
20rates,21ridge coefficients. Secondary history concatenates4recent20msvectors:
80features,81coefficients. Identical external memory budgets across C0/C1.
Observed population rates are for the100recorded cells, not all1000neurons.
Full-population currents/voltages never enter any predictor. Silent periods have
zero delivered stimulus, not absent spontaneous neural firing.

Cue-end, distractor-end and final representations use separate readouts with the
same fit/validation/test trials. Curves therefore show separately decodable
information, not predictions of one fixed decoder at three times. Delays each
have their own fitted decoder; no held-out delay interpolation/extrapolation claim.
Covariance and effective dimension use fitting features only; rank is limited by
16fit trials (at most15after centering). High rank is not evidence of computation.

## Ablation access limitation

All recurrence means BOTH excitatory and inhibitory transmissions are disabled.
Because original recording/stimulation membership is disjoint, recorded cells
in C1 also lack a direct stimulus path. This is a correctly implemented matched
unconnected control, but does NOT isolate recurrent memory from feedforward
stimulus propagation. Cue-end decodability is included to expose this limitation.
No compensating background/current was added. A future separately preregistered
feedforward-access-matched reservoir could distinguish these explanations.
C7is identical to C1here and is not double-counted as independent evidence.

## Controls and secondary tasks

C2receives four zero final-window currents; it must score50% on balanced recall.
C3/C4explicitly retain both symbols; they are reference algorithms with external
memory, not same-information neural decoders. C5is an offline per-split trial-
feature permutation negative control, not a deployable causal forecaster; it
breaks label/representation correspondence. Primary models never receive other
trials' future observations. C6shuffles fit/validation labels, leaves true test
labels for final scoring. Neither control is selected to be near chance.

Delayed match and TWO-symbol parity are complements on the same stimulus trials;
they are not independent tasks supporting a general computing claim. Binary lag
probe classification at lags1,2,4,8is not classical continuous-input memory capacity.
It has a separately declared continuous drive,16bin warmup and chronological
128fit/48validation/64test bins. Primary recall uses independent resets instead.

## Reset/randomness qualification

Network.restore(...,restore_random_state=False) is explicit in the inherited
engine. This alone would not replay arbitrary random streams. Here no Brian
random expressions are used: OU innovations are rebuilt from network/role4/
replicate/block SeedSequence keys, with noise-block cursor reset after restore.
Primary trial replicateIDs are distinct and matched across conditions; all other
initial neural state/queues/clock/cursors reset. Exact replay and inactive-current
checks passed; timestamps/counts are independently reconstructed from artifacts.
See the inspected [Brian2 2.10.1 Network API](https://brian2.readthedocs.io/en/2.10.1/reference/brian2.core.network.Network.html)
(accessed2026-11-05). Python/external generators are not presumed restored by Brian.

No biological memory, hardware qualification or asymptotic capacity is claimed.

## Observed D80 diagnostics

| Network | Condition | Recorded E mean Hz | Recorded I mean Hz | Fit rank | Effective dimension | Cue-end accuracy % | Distractor-end accuracy % |
|---|---|---:|---:|---:|---:|---:|---:|
| 14000 | C0 | 15.160 | 15.733 | 15 | 8.372 | 43.75 | 31.25 |
| 14000 | C1 | 25.229 | 25.094 | 15 | 8.286 | 56.25 | 56.25 |
| 14001 | C0 | 13.603 | 12.340 | 15 | 8.831 | 50.00 | 31.25 |
| 14001 | C1 | 25.291 | 24.639 | 15 | 8.168 | 43.75 | 18.75 |

Disconnection increases observed activity here, but removes both E and I paths; these data alone do not identify inhibition as the cause. No rate compensation was applied. Effective dimensions are similar, all ranks saturate the16sample centered-rank ceiling15, and neither implies cue memory. Cue-end decodability itself is weak/variable, which substantially limits a retention interpretation. The apparent final-window advantage is not a verified persistence timescale.

The raw full-trajectory count records retain activity distributions and silent-input bins for every trial. Rates are not a direct MEA voltage measurement. No runaway/nonfinite-feature gate triggered; model refractory limits remain unchanged. Classifier alpha selections and all3validation scores are preserved per model; no alpha was reselected using test performance.

176task prediction archives plus16lag archives independently verified. All cue-end/distractor-end/final/history features reconstruct exactly from recorded counts, and final readout timestamps follow completed observations. Every current trajectory respects original bounds and4.8pA·s task exposure. Both condition banks share network-parameter hashes, delivered schedules and per-trial OU hashes. Reset replay passed with inactive transmission and zero recurrent currents.

The primary effect was9.375pp with descriptive95%CI[-30.332,49.082]pp. This is not significant evidence of useful recurrent memory. The history-buffer result is secondary and may store recent activity outside the network. Some shuffled controls exceed unshuffled scores in this small sample; no robust representation advantage over noise controls is established.
