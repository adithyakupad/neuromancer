# M014 prospective reservoir-computing pilot and confirmation gate

Base ffe6b4f4a71ba7a58864bb92ada25b7c0a656c0b, branch
research/v2-m014-reservoir-computing. No old source, tests or evidence edits.
M012 qualified test source724eec11; its closing source05ad832c is inherited.
M013 remains a two-network inconclusive plasticity pilot. No plasticity is active
or constructed in M014. Personal style guide read from optional branch only.

## Primary hypothesis / scope
At80ms delay on both sides of a distractor, original recurrent neural features
improve held-out binary cue recall over recurrence-disabled features by>=5pp,
with paired network-level95%Student-t CI lower>0. No bin/trial pseudoreplication.
Pilot networks14000,14001 only, root20261105. n2 yields inadequate network precision
regardless of the point estimate; never label this confirmatory scientific PASS.
Confirmation design (NOT automatically authorized):64new networks14100–14163,
64fit/32validation/128test trials per delay/condition, network-mean CI target
half-width5pp under planning SD20pp (normal approximation requires62networks;
64is an engineering planning choice, not a known variance). Forecast all confirmation
work with2x measured headroom against3600s cap; if above cap, confirmation NOT RUN.
No M013 or V1locked IDs100–119 are used for confirmation/tuning.

## Timeline / independent trials
Original1000-neuron E/I LIF,100us integration,20msbins, all original parameters,
connectivity, noise and actuator limits. Each trial restores initial neural state,
queues, clock, monitor cursors and observation-filter state. Config's replicate_id
is replaced by a distinct trial noise identity AFTER restore; network parameters
remain fixed (roles0–3 use replicate0). Brian restore_random_state=False is deliberate:
no Brian stochastic expressions exist; explicit OU blocks derive from SeedSequence
(network,role4,replicate,block). Network API documentation inspected2026-11-04:
https://brian2.readthedocs.io/en/2.10.1/reference/brian2.core.network.Network.html
Brian RNG restoration alone would not restore external generators. Verify replay.

Cue0channel0, cue1channel1; distractor0channel2,distractor1channel3.
Each pulse is[30,60,30,0]pA over4bins =80ms, with identical exposure2.4pA*s.
Both silent delays use D in[20,40,80,160]ms. Final observation40ms; duration200+2Dms.
No commanded current during either silent delay/final window; spontaneous background
firing is expected and measured, not called silence of neural activity. Timing and
energy are label-independent, including ramp-down tails. All transitions explicitly
validated. Trials reset rather than carrying state between labels. Two symbols
are exactly factorial-balanced within EVERY split/delay; the distractor is sampled
with a separate RNG role and permutation within cue strata, giving exact empirical
independence, not two globally dependent streams. No outcome-dependent ordering.
Each split order is randomized; reset removes prior-trial state as a cause.

Pilot each delay:16fit,8validation,16test trials per neural condition. Role200cue,
201distractor,202order,203controls; noise ID140000+delay_index*1000+split_index*100+
trial_index, identical across paired conditions. No mixed-delay training or held-out
interpolation claim: readouts fit separately per delay. Delay curves are matched-task
comparisons, not unmeasured delay generalization.

## Features / readouts / controls
A primary:20-channel rate vector from summed counts in final40ms /(.04s*5neurons),
shape20,21ridge coefficients including intercept. No symbols, label, time, trialID,
hidden voltage/current or future events enter features.
B secondary: flatten last4completed20msrate vectors (80ms,shape80,81coefficients).
Identical budgets for recurrent and disabled conditions. Includes recent distractor
activity at shortest delays; no claim of purely intrinsic memory for B.
All scaling fit-only; ridge alpha[.1,1,10], intercept penalized, threshold.5;
validation balanced accuracy chooses FIRST maximum. Predictions generated before
passing held-out labels to scoring. Separate task targets have separate readouts.

C0original frozen recurrence. C1both excitatory/inhibitory synaptic pathways
inactive from t0; connectivity/weights/OU/stimulation/neuron parameters unchanged.
Reapply inactive flags after each restore and independently verify no synaptic
transmission. No firing-rate retuning. C7unconnected neurons is identical to C1,
so not duplicated as a falsely independent control.
C2current input:four zero currents during final window, chance if no leakage.
C3linear full history:[cue,distractor]; C4nonlinear:[cue,distractor,cue*distractor],
with access to actual complete input information, not neural metadata.
C5per-split permutation of neural trial features, frozen role203; labels unchanged.
C6fit AND validation labels independently shuffled, true reserved labels scored.
Fit/validation balance preserved, no test-label selection. C5/C6 diagnostic controls
may fluctuate with finite samples; current-input-only must be exactly50% on balanced
splits or stop for leakage. No new hyperparameter search beyond the fixed3alphas.

## Secondary tasks and explanatory diagnostics
On the same two-symbol trajectories: delayed match-to-sample target cue==distractor;
two-symbol temporal parity target cue XOR distractor. They are logical complements,
not independent corroborating tasks. No claim of three-symbol parity.
Binary lag-memory probe separately drives256bins with current30pA on channel0/1,
128zeros/128ones randomized, roles210inputs and211noise; no resets within this probe.
After16warmup bins,128fit/48validation/64test bins chronologically split; lags1,2,4,8.
Only completed20channel counts at current bin supplied; target is past binary input.
Report classification accuracy by lag, NOT classical continuous linear memory capacity.
This separately declared continuous-drive task does not change independent-reset
interpretation of the primary trial experiment.

Diagnostics (not rescue endpoints):recorded E/I rate distributions and ablation
changes, source-native full-population spike-rate summaries if obtainable without
altering observation access; cue accuracy at cue end/distractor end/final (separate
readouts using same splits), feature covariance/rank/effective dimension, saturation,
alpha sensitivity, reset-to-reset history independence and condition costs.
Effective dimension=(sum eigenvalues)^2/sum(eigenvalues^2), zero if all zero.
No hidden simulator values enter fitting. Explicit-history reference accuracy is
not neural advantage. No weight changes/plasticity authorized.

## Engineering/resource gates before acquisition
Deterministic reduced task and neural fixtures:factorial balance, independent RNG
roles, energy/slew, time alignment, final/history shapes, future-data mutation,
readout-label mutation, ablation, paired initialization/noise and exact replay.
Frozen equations/runtime checks must pass before neural pilot; control absent,
invalid current, failed replay, nonfinite features or archive modification =>HOLD.

Development qualification cap180s includes construction/representative trial probe;
full historical suite separate180s cap under external watchdog. Pilot900s absolute
suspend-inclusive supervisor deadline, unchanged cleanup reservation/graces, outer
watchdog905s. <=2GiB measured worker peak and <=200MiB artifacts; persist per split.
Forecast total simulated duration:cue tasks230.4s (sum delay durations1.4s*40trials*
2networks*2conditions=224s; arithmetic total is224s), plus20.48s binary probe =>244.48s.
The230.4text is not a second allowance:244.48total is authoritative. Before launch
record actual construction/trial throughput; require2x forecast+60s <=900s. No cap
extension or outcome-dependent reduction. Full confirmation forecast separately.
All failed attempts retained, no replace-seed reruns. Stage resources never reset
inside a stage. No merge/tag/publication or automatic Day3.
