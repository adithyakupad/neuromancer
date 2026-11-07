# M015 causal memory validation

Engineering **PASS** for the graph, replay and access experiment. Scientific
**HOLD** for retention interpretation. The cue qualification gate failed in
both development networks, so the retention comparison is **NOT RUN**. The
experiment leaves the primary recurrence effect and interval unmeasured.

The base is `9cde9c24d0e2db4c76d70741b4427c1d77962453`. Acquisition used
`6298ffac9ff1df1bacf5cbfe286861d23b822f61` on
`research/v2-m015-causal-validation`. The [protocol](../../docs/research/M015_CAUSAL_MEMORY_PROTOCOL.md)
was committed before acquisition. Physical Git blob checks verified all 38,504
base paths, including V1, M013 and M014 data, code and reports.

## What the intervention changes

All variants use the original 1,000-neuron Brian2 E/I LIF realization, 100 µs
integration, 20 ms bins and the original four input and twenty recording channels.
C0 retains the recurrent graph. C1 deactivates both synapse objects. C2 retains
only edges going forward through the stimulated E, unrecorded E, unrecorded I
and recorded E/I layers. The retained edges have the original weights and delays.
Other Brian edge slots have zero weight. Neither C2 nor C1 adds current directly
to recorded cells. Plasticity stays inactive.

| Network | Condition | Effective E edges | Effective I edges | Largest strongly connected component |
|---|---|---:|---:|---:|
| 15000 | C0 | 39,687 | 10,125 | 1,000 |
| 15000 | C1 | 0 | 0 | 1 |
| 15000 | C2 | 15,155 | 940 | 1 |
| 15001 | C0 | 40,183 | 9,989 | 1,000 |
| 15001 | C1 | 0 | 0 | 1 |
| 15001 | C2 | 15,418 | 879 | 1 |

Each of the four stimulus channels reaches all 100 recorded cells in C2, with
one or two hops along the shortest paths. C1 reaches none. The independent
verifier reconstructs a topological ordering from effective edge arrays, checks
recorder reachability, and checks that each retained signed weight and delay
occurs in C0. Thus C2 has a functioning path with verified structural access,
while its measured activity and cue signal fall short of functional matching.
Removing feedback also removes many E and I edges. This experiment cannot
assign the firing-rate change to one of those losses. The original stimulus and
recorder memberships remain disjoint.
[Connectivity diagram](evidence/m015/connectivity.png)

## Cue access results

Two independent networks, each with 16 fit, 8 validation and 16 held-out
balanced cue trials per condition, plus 16 paired sham trajectories.
There are 240 cue and 96 sham trajectories. Trials share the same initial
state and explicit role-4 OU innovation hashes across conditions and between
cue and sham. Reset restores state, queues and the observation cursor.
The replicate key changes for each trial, and the inherited engine
regenerates innovations with Brian RNG restoration disabled.

The decoder uses 20 recorded rate features from the final 40 ms of the
80 ms cue. Fit data determine scaling, validation chooses ridge strength,
and held-out labels score frozen predictions. The verifier recomputes the
features and ridge selection from archived counts and symbols using a
separate linear solve.

| Network | Condition | Cue accuracy | Mean E / I rate (Hz) | Class 0 / 1 evoked RMS (Hz) | Fit rank / effective dimension |
|---|---|---:|---:|---:|---:|
| 15000 | C0 | 37.50% | 11.875 / 14.766 | 1.169 / 1.411 | 15 / 7.049 |
| 15000 | C1 | 62.50% | 25.684 / 25.156 | 0 / 0 | 15 / 8.859 |
| 15000 | C2 | 37.50% | 1.055 / 1.328 | 0.395 / 0.395 | 10 / 5.029 |
| 15001 | C0 | 62.50% | 14.004 / 18.125 | 1.563 / 1.398 | 15 / 8.060 |
| 15001 | C1 | 43.75% | 25.703 / 24.922 | 0 / 0 | 15 / 8.071 |
| 15001 | C2 | 62.50% | 0.625 / 1.641 | 0.395 / 0.395 | 9 / 5.568 |

C1 has exact equality of cue and sham counts, including the network with
62.50% test accuracy. Finite-sample decoding alone can therefore suggest cue
information even in the verified disconnected null. Both C0 and C2 missed
68.75% cue accuracy. C2's class-specific contrasts missed 1 Hz, and its pooled
cue-window firing was 8.91% and 5.58% of C0, outside the allowed two-thirds to
1.5 ratio. The maximum across held-out exposed 20-ms channel bins was 50 Hz
in C0/C1 and 30 Hz in C2. Their 95th percentiles were 30, 40 and 20 Hz,
respectively, in both networks. Rates were finite and passed the stability
gate. Covariance matrices and validation scores are archived. Effective
dimension reflects 16 fitting trials and is descriptive.
[Cue, rate and evoked response figure](evidence/m015/cue_access.png)

Identical point accuracies in C0 and C2 do not establish equivalence.
C0 itself failed the observable cue requirement. The result supports
weak cue encoding under this interface, alongside a strong firing-rate
change from the DAG intervention. Neither result tests retention. No
distractor, final-window score, delay curve, paired retention effect or
retention CI is available. The frozen +5 pp effect and paired 95% CI
criteria remain unevaluated. The two-network access sample has insufficient
precision for a confirmatory inference. All 64 proposed confirmation
networks and the historically locked cohorts remain unopened. The frozen
stop ruled out redesigning a replacement control after inspecting this
access bank. A separately preregistered design would need a demonstrably
decodable cue and a feedforward control that preserves observable input
access without the large activity imbalance.

## Qualification and resources

218 regression tests passed with 46 warnings in 44.25 s of pytest time.
The three added tests check graph/delay preservation, exact reset replay
and rejection of weak encoding despite evoked activity. Independent
reconstruction verified all 336 trajectories, stim/sham contrast, noise
pairing, stimulus bounds and availability timestamps. The independent
reduced simulator benchmark qualified separately.
[Cross-simulator report](M015_CROSS_SIMULATOR.md)

| Supervised stage | Wall seconds | Fixed cap (s) |
|---|---:|---:|
| Representative benchmark | 2.827 | 120 |
| Regression | 44.501 | 180 |
| Cue access | 79.552 | 420 |
| Reduced simulator | 1.448 | 120 |

The three 360-ms benchmark trials took 0.467, 0.384 and 0.393 s, with
0.0247 s construction. The conservative forecasts were 344.35 s for
access and 703.26 s for conditional retention. Access simulated 26.88 s,
used 1,381,449,728 bytes peak worker RSS and recorded 2,536,138 bytes
at acquisition close, before reporting plots and manifests. Independent
process checks verified cleanup and deadlines. No watchdog intervention.
Wall times here are desktop simulation measurements.

## Reproduction

Use the pinned repository environment and an empty output directory.
The first command below verifies the archived outcomes and regenerates figures.
The subsequent commands repeat the development benchmark, cue access and the
reduced comparison. The retention launcher checks the saved cue gate and
rejects this cohort's HOLD.

```sh
PYTHONPATH=src python -m pytest -q
MPLCONFIGDIR=/tmp/m015-mpl python scripts/m015_verify.py reports/research/evidence/m015
PYTHONPATH=src python scripts/m014_supervise.py /tmp/m015-benchmark 120 python scripts/m015_memory.py benchmark /tmp/m015-benchmark
PYTHONPATH=src python scripts/m014_supervise.py /tmp/m015-access 420 python scripts/m015_memory.py access /tmp/m015-access /tmp/m015-benchmark/benchmark.json
PYTHONPATH=src python scripts/m014_supervise.py /tmp/m015-cross 120 python scripts/m015_cross_simulator.py /tmp/m015-cross
```

Interview mechanisms worth defending are structural versus functional
access, matched-noise interventions versus finite-sample decoder scores,
and the distinction between propagation, initial encoding and retention.
These are simulated observations.
