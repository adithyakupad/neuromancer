# M013 — functional plasticity pilot

**Engineering: PASS for the executed pilot instrument. Scientific superiority: NOT QUALIFIED / INCONCLUSIVE.** Confirmatory cohort NOT RUN.

Base05ad832c7c062ba5cdd8d1d9e38129410ecafa32. Protocolffc5c7b8. Acquisition source`f740b9d936abb2cac5597e0edac7cbe174c7a6b1`. Final report/source commit is identified in the handoff; nothing is merged/published.

## Frozen question and design

Does reward-modulated E/E pair STDP improve held-out delayed XOR representation versus frozen recurrence? Minimum5pp and positive paired95%CI were frozen before acquisition. Two independent networks (13000,13001) provide only a pilot, not useful confirmatory precision. No outcome-based tuning, exclusions or replacement seeds. Original1000-neuron Brian2 network,100us integration,20msbins and original4channel stimulation constraints are unchanged. Plasticity is additive and optional.

See the committed protocol for equations, role seeds, schedules and selected defaults. Reward uses a training-only online linear decoder; probe/readout fitting is a separate stage. Trial IDs and labels never enter neural stimuli beyond the two input symbols. All classes have equal delivered current exposure. Standardized probe ridge fitting uses16trials,8validation trials select among3fixed penalties;16reserved trials score the primary outcome. Neither decoder nor synapses update during testing.

Two networks × five reservoirs × (32training+16probe+8validation+16primary test+16delay test)=880trials;320training,160probe,80validation,160primary-test and160delay-test trials. Each network is one replicate; no bin/trial pseudoreplication. The20ms/100msdelay tests reuse the frozen40ms-trained representation/readout.

## Complete per-network primary and delay results

| Network | Condition | Test % | Delay20 % | Delay100 % | Changed E/E weights | Bound fraction |
|---|---|---:|---:|---:|---:|---:|
| 13000 | C0 | 31.25 | 62.50 | 50.00 | 0 | 0.000 |
| 13000 | C1 | 56.25 | 75.00 | 37.50 | 31556 | 0.000 |
| 13000 | C2 | 62.50 | 50.00 | 75.00 | 31659 | 0.000 |
| 13000 | C3 | 31.25 | 62.50 | 37.50 | 31481 | 0.000 |
| 13000 | C4 | 50.00 | 50.00 | 62.50 | 31497 | 0.000 |
| 13001 | C0 | 56.25 | 50.00 | 75.00 | 0 | 0.000 |
| 13001 | C1 | 56.25 | 75.00 | 37.50 | 31492 | 0.000 |
| 13001 | C2 | 68.75 | 62.50 | 50.00 | 31169 | 0.000 |
| 13001 | C3 | 31.25 | 12.50 | 50.00 | 31256 | 0.000 |
| 13001 | C4 | 43.75 | 37.50 | 12.50 | 31281 | 0.000 |

C0frozen;C1reward;C2unmodulated eligibility-based STDP;C3within-minibatch reward permutation;C4random training labels. C7 is feature centering, not a causal activity-matched network. Its per-network scores are in independent_analysis.json.

| Model | Mean primary accuracy % |
|---|---:|
| C0 | 43.750 |
| C1 | 56.250 |
| C2 | 65.625 |
| C3 | 31.250 |
| C4 | 46.875 |
| C5 memoryless B | 50.000 |
| C6 linear history | 50.000 |
| Nonlinear history [A,B,A×B] | 100.000 |

C1−C0 effects: [25.0, 0.0]pp; mean12.50pp. Descriptive paired Student-t95%CI[-146.32755920218366, 171.32755920218366]pp,df1. The interval is deliberately not clipped to feasible effects; the normal-network assumption is unverifiable with n2. It is extremely imprecise and includes zero. The positive mean exceeds5pp but fails the positive-CI gate. Confirmatory superiority is NOT demonstrated. This is not evidence that the true effect is zero.

C2 performed better than C1 in both pilot networks. That descriptive finding limits reward-specific interpretation; weight changes alone are not functional learning. C3/C4 controls and delay results are heterogeneous. Nonlinear input history solves this simple task without neurons, so reservoir accuracy is not biological intelligence or computational advantage.

## Mechanistic and activity findings

No synapses reached either bound; each plastic condition changed many E/E weights. Initial/final arrays preserve every connection-level change. Recorded E/I mean rates, per-network confusions, conditioning diagnostics, exposures, complete spike-count bins, coefficients, predictions and split symbols are saved. These are partial-recording rates, not evaluator full-population rates. No full-population voltage/current recording was added. No causal activity-matched experiment was performed. Training curves reflect training-decoder behavior, not held-out learning curves.

## Resource and failure accounting

Qualified-clock resumed worker elapsed202.660554s; elapsed from original deadline creation through completion232.833172s. Fixed900s deadline retained across pre-integration scalar-type repair. Remaining667.166828s. No deadline extension, cleanup failure or outer-watchdog intervention. Resource probe forecast447.230s; actual simulated duration179.2s. Resource accounting includes separate120s qualification budget, no scientific acquisition there.

Measured probe construction0.569703s,1s neural integration1.048650s,peakRSS874823680bytes. Trace-array estimate1024640bytes excludes indices/queues/network copies. Pilot checks cumulative process peak after every condition against2GiB and output against200MiB; none failed. Exact per-condition RSS values were not archived, so no exact pilot peak-memory claim is made. Evidence before report generation was9806604bytes. Full regression testing overlapped acquisition; timings are workload measurements, not isolated simulator benchmarks. All early failed development logs and initial rejected pilot process remain.

## Verification and reproduction

Final suite211passed,46warnings,58.45s. Mechanism/task qualification10passed,8warnings,3.09s. pip check passes. Historical38057tracked paths hash unchanged. Public observations match the original network with plasticity disabled; trace/weight checkpoint replay matches exactly. No old test expectation was edited. Raw final logs/XML retain warnings. Evidence-only V1 reproduction preserves its negative findings; see v1_reproduction/reproduction.json for actual byte comparisons.

```sh
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python scripts/m013_analyze.py reports/research/evidence/m013/pilot_typed
PYTHONPATH=src python scripts/reproduce_v1_evidence.py --output /tmp/m013-v1-reproduction
```

Fresh pilot acquisition requires the committed protocol, passing mechanism gates and an externally created900sDeadline propagated through the existing supervisor. Do not invoke the pilot directly without NEUROMANCER_DEADLINE_NS, NEUROMANCER_DEADLINE_CLOCK and NEUROMANCER_STOP_FILE. Exact supervisor commands and returned records are preserved; no default unbounded acquisition entry point exists.

## Limitations and next falsifiable experiment

This is a small, short-training, single-family simulation pilot. Fixed engineering defaults were not physiologically validated; pair timing and reward credit assignment are assumptions. Trace persistence across trials, no initial burn-in and small probe/validation sets may affect results. C7 is only a representation diagnostic. No physical MEA, living neurons, Neuralink/CL hardware, biological plasticity or hard-real-time operation was validated. No V1locked IDs100–119 were opened. Agent-generated code is not attributed as personally handwritten.

Next: independently preregister a substantially larger, resource-justified new cohort to compare C1against bothC0andC2, with fixed training duration and delay bank. Reward-specific superiority should not be inferred unless it also exceeds matched unmodulated/shuffled controls. Do not reuse this pilot as an untouched confirmation cohort or retune and call its tests fresh. No Day2 study is authorized here.

To defend this work: explain pre/post arrival ordering, eligibility decay at reward time, reward-to-synapse credit assignment, why the probe decoder is separate, why XOR needs nonlinear history, what common exogenous noise does and does not match, why two networks cannot establish superiority, and why many changed weights do not prove task-directed learning.

## C7 diagnostic and closure

| Network | Underlying condition | Centered-feature accuracy % |
|---|---|---:|
| 13000 | C0 | 37.50 |
| 13000 | C1 | 43.75 |
| 13000 | C2 | 62.50 |
| 13000 | C3 | 50.00 |
| 13000 | C4 | 50.00 |
| 13001 | C0 | 62.50 |
| 13001 | C1 | 37.50 |
| 13001 | C2 | 75.00 |
| 13001 | C3 | 31.25 |
| 13001 | C4 | 50.00 |

Independent parameter hashes and every time-indexed noise-block hash match across C0–C4 within each network. All owned worker groups were checked absent after acquisition. V1 evidence reproduction PASS: four numerical artifacts and four figures byte-identical; no neural V1 reacquisition. The final source/evidence commit is reported in the handoff. No hosted CI success is claimed for this new research branch.
