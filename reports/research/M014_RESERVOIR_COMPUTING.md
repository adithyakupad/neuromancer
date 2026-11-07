# M014 — frozen reservoir temporal-memory pilot

**Engineering PASS for the executed pilot benchmark. Scientific result INCONCLUSIVE; confirmatory acquisition NOT RUN.**

Base`ffe6b4f4a71ba7a58864bb92ada25b7c0a656c0b`; protocol0bb74199; acquisition source5cdb9b27 (full manifest.json). Final documentation/evidence commit is identified in the handoff. New branch research/v2-m014-reservoir-computing. No merge, tag, publication or Day3 work.

## Scientific design

Does final recorded spiking activity retain cue information after delay+distractor+delay, beyond recurrence-disabled cells? Unchanged1000-neuron Brian2 E/I network,100us integration,20msbins,20virtual channels. No plasticity. Cue channels0/1 and independent distractor channels2/3 each use30/60/30/0pA pulses;4.8pA·s per trial, class-independent. Silent periods have zero commanded current but spontaneous activity. Each trial restores neural state and uses fresh explicitly keyed OU noise; same noise and initial realization across paired neural conditions. No trial-to-trial state carryover in primary recall.

Primary is80ms on BOTH sides of distractor: mean network-balanced accuracy C0−C1,>=5percentage points and positive paired95%CI. Two new pilot networks14000/14001, not M013networks. Each delay and condition has16fit,8validation,16reserved test trials;4delays ×2networks ×2conditions =640independent-reset trajectories:256fit,128validation,256test. At primary delay:64test trials total across bothconditions/twonetworks,16per network/condition. Those are NOT64independent neural networks.

Each condition also has one256bin continuous-drive binary lag probe:4streams,1024bins total. This is a separately declared secondary task, not a change to primary reset interpretation. Total244.48simulated seconds. Match/parity readouts reuse primary trajectories; no extra independent trials are implied.

Final-window feature20rates from40ms;21coefficients. Secondary recent80ms history80features,81coefficients. Standardize using fitting observations only; ridge[.1,1,10], penalized intercept, validation selects first maximum, threshold.5. Targets/metadata/hidden states/future events are absent from neural features. Test labels are used for scoring after predictions; evaluator knows task symbols, but never supplies them to neural readout features.

## Primary comparison

| Network | Recurrent C0 % | Recurrence-disabled C1 % | Paired effect pp |
|---|---:|---:|---:|
| 14000 | 43.75 | 37.50 | 6.25 |
| 14001 | 68.75 | 56.25 | 12.50 |

Means56.25% versus46.875%; effect9.375pp. Descriptive paired Student-t95%CI[-30.331889800545916, 49.081889800545916]pp,df1. Point estimate exceeds5pp, but uncertainty gate FAILS. With two networks the normal-network assumption cannot be checked; this interval is not evidence of absence or confirmatory support. Both paired effects are positive, but that does not make n2 a qualified cohort.

The64-network confirmation design was not opened: forecast118146.503s exceeds frozen3600s budget. Planning assumes20pp network SD and5ppCI half-width; neither planning variance nor actual precision is established by this pilot. No outcome-selected sample-size reduction or budget extension.

## Complete final-window delay bank

| Network | Condition | 20ms % | 40ms % | 80ms % | 160ms % |
|---|---|---:|---:|---:|---:|
| 14000 | C0 | 68.75 | 62.50 | 43.75 | 56.25 |
| 14000 | C1 | 37.50 | 56.25 | 37.50 | 56.25 |
| 14001 | C0 | 50.00 | 43.75 | 68.75 | 56.25 |
| 14001 | C1 | 37.50 | 68.75 | 56.25 | 56.25 |

Delay curves are not monotonic and do not establish a reliable retention timescale. Readouts were separately fit at each delay. No unseen-delay generalization was tested. Full per-network/per-delay/per-model outcomes and regularization selections are in classification_metrics.csv and prediction NPZs. No poorly responsive network was excluded.

## Controls at the primary delay (network means)

| Source condition | Final A % | History B % | Current C2 % | Full linear C3 % | Full nonlinear C4 % | Feature shuffle C5 % | Label shuffle C6 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| C0 | 56.25 | 62.50 | 50.00 | 100.00 | 100.00 | 43.75 | 46.88 |
| C1 | 46.88 | 46.88 | 50.00 | 100.00 | 100.00 | 59.38 | 53.12 |

C2scores exactly50% throughout the entire bank: no current-input leakage observed. C3/C4have actual cue history and score100%; their duplicates across neural conditions are NOT independent replicates. C1is also the unconnected C7control. Shuffle controls fluctuate above/below chance; they do not support a robust neural decoding advantage. C5is an offline trial-assignment negative control, not a causal deployed forecast.

## Secondary tasks

| Network | Condition | Match at80 % | Two-symbol parity at80 % | Lag1 % | Lag2 % | Lag4 % | Lag8 % |
|---|---|---:|---:|---:|---:|---:|---:|
| 14000 | C0 | 75.00 | 75.00 | 44.68 | 60.12 | 40.64 | 53.10 |
| 14000 | C1 | 56.25 | 56.25 | 49.26 | 49.01 | 50.10 | 52.95 |
| 14001 | C0 | 43.75 | 50.00 | 41.47 | 49.61 | 56.67 | 48.41 |
| 14001 | C1 | 68.75 | 68.75 | 42.06 | 48.92 | 57.94 | 41.27 |

Match and two-symbol parity are complementary labels on the same trajectories, not independent evidence. Penalizing the intercept can make their thresholded scores differ. Binary lag accuracy is NOT classical linear memory capacity. These secondary outcomes have no preregistered superiority gates and cannot rescue primary uncertainty.

## Verification / resources

215tests passed,46warnings,41.54s. Four reduced/new tests passed after a preserved test-only unit mismatch repair. Source-neural replay, current limits, causal timing, zero synaptic currents during ablation and unchanged weights were checked. Full historical regression ran under180s supervision; no watchdog intervention. Independent analysis verified176prediction archives plus16lag archives, reconstructed features from saved counts, checked factorial labels, current exposure, timestamps, paired noise hashes and identical network-parameter hashes. All owned worker groups were independently checked absent.

Actual worker elapsed248.046564s; supervisor elapsed248.712636s; pilot peakRSS1492303872bytes; artifact size at acquisition close6072866bytes. These passed900s/2GiB/200MiB gates. Total244.48simulated seconds; elapsed includes resets, recording, readouts and logging, not pure integration throughput. No hard real-time qualification. Supervised developer probe used180s cap; three360ms trials actually took[.514785,.371963,.366565]s, construction.027783s, peakRSS1016561664bytes; conservative pilot forecast777.719s. Exact stage clocks/budgets/cleanup records are retained.

All38155starting-source tracked paths hash unchanged, including V1 and M013code/reports/numerical archives. No scientific dependencies upgraded or old tests changed. Physical suspend was not deliberately tested. Hosted CI success for this new branch is not claimed.

## Reproduce

Use the pinned environment and project source:

```sh
python -m pip install -r requirements-v1.txt
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python scripts/m014_analyze.py reports/research/evidence/m014/pilot
PYTHONPATH=src python scripts/m014_supervise.py /tmp/m014-new-pilot 900 python scripts/m014_pilot.py /tmp/m014-new-pilot
```

The last command acquires the frozen PILOT only and requires a new empty output directory, passing gates and qualified clock. It does not authorize confirmation. Source hashes, seeds, environment, predictions, raw counts, actions and budgets are in evidence/m014. Figures are generated solely from acquired results.

## Interpretation / next falsifiable experiment

No confirmatory evidence of useful recurrent cue memory was established. Small-nnoise, weak observed cue encoding, modest trial counts and changed firing rates after disconnection limit interpretation. Full recurrent ablation also removes stimulus access to disjoint recorded cells: it cannot alone distinguish recurrence-specific memory from ordinary propagation. No matching current was added. A future separately preregistered access-matched feedforward control plus reliable cue-end decoding would be the smallest mechanistic discriminator; do not tune this cohort and call it confirmation.

This simulated benchmark does not demonstrate biological memory, neural intelligence, plasticity, hardware-safe stimulation or Neuralink/CL1compatibility. No locked V1networks100–119 or confirmation networks14100–14163 were opened. No Day3 work is started.

Interview points: distinguish intrinsic neural state from an external readout history buffer; explain reset/OU replay versus Brian RNG restoration; explain why ablation changes input access/activity and why a positive point estimate with n2cannot establish recurrent-memory superiority.

### Audit details

The first protocol's resource prose contains a230.4s typo, explicitly corrected
in the same preregistration to the authoritative244.48s total. Schedules, fixed
trial identities and the forecast formula were unambiguous before acquisition;
actual244.48s matches that formula. No endpoint or resource cap changed afterward.
The only failed development test compared a unit-bearing amp array with a
unitless SI array; both sides now explicitly compare pA. Its original failure log
is retained, and no ablation or replay discrepancy was masked.

Figures: evidence/m014/pilot/reservoir_diagnostics.png. All per-model numeric
predictions, coefficients, scaler parameters, alpha validation scores and source
features remain beside figures, alongside raw recorded counts and action receipts.
The estimator never consumes test labels while fitting or selecting models.
Code is agent-generated and should be independently understood before presenting
it as work one can defend; it is not represented as personally handwritten code.
