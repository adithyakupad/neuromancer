# M004 — Online identification and residual-shift detection

**Execution PASS, with a documented pre-scoring timing clarification. Operational predictive-adaptation H1 PASS; residual-shift detection H2 PASS in reserved development and prospectively frozen validation.** Slow RLS improved prospective1s mean-rate prediction after hidden efficacy loss without breaching stationary/pre-change guardrails. This is partial predictive compensation: interval calibration remained poor, sustained recovery was uncommon, and the validation paired-effect benefit was inconclusive. No controller, neural plasticity, biological experiment or original V0 authority qualification follows.

## Repository, preservation and preregistration

Startingclean `research/m003-2-state-dependence`, exactHEAD **1fe8f6bd0a1e057b8bbe10cd7d10d49e33c1a2d2**. Created `research/m004-online-identification`. All2481historical files—including failed V0 target authority/calibration, M003 results, and M003.1/M003.2 model-superiority negatives—remain byte-identical. No history reset, overwrite, merge or push.

Protocol [008_M004_ONLINE_IDENTIFICATION_PROTOCOL.md](../docs/research/008_M004_ONLINE_IDENTIFICATION_PROTOCOL.md) committed **0425ad0** before neural acquisition; implementation/acquisition **adb4813**. Before acquisition an editorial question-mark string was corrected to15.8s; numerical FIT index790 was already authoritative and never changed. Separate [timing clarification001](evidence/m004/PREREGISTRATION_CLARIFICATION_001.md), committed **f2fb6ff** while acquisition ran but before any replay/tuning/scientific scoring, resolves a causal boundary defect: an alarm ending exactly59s uses exclusively pre-change observations. Such alarms count false; timely detection is **59<t<=69s**. No threshold, model, trajectory, seed or hypothesis changed. The original protocol remains preserved.

Selected settings were committed at **5ac0f5c06fbeffb8b8535b992708f6afe32b3fd7** before validation acquisition. Validation provenance records that exact commit and selectionhash; independent verification checks the committed JSON. Final evidence/publication revisions appear in closure/final mission response. Entirely simulated research, not offline biological recordings or living preparations.

## Frozen questions, information access and gates

H1 primary: improve prospective post-change **1s mean absolute observed-rate prediction**, not merely ordinary20ms next-step error. Require mean paired relative benefit>=10%, absolute>=.04Hz², paired network95% lower benefitCI>0, positive>=8/10 development or>=4/5 validation networks. Stationary post-window mean relative harm<=5%, upper95% harmCI<=10%; pre-change mean harm<=5%. Relative denominator floor.04Hz², never activated. Both cohorts must pass. Secondary same-origin intervention contrasts separately test whether improvements concern causal responses; they cannot replace or rescue primary gates.

H2 independently: timely detection>=80%, median network-mean censored delay<=10s, stationary false-alarm mean<=1/min and upper95% bound<=2/min, and positive paired network95% lower bound for timely-loss detection probability minus stationary alarm probability in the matched10s window. Misses censored20s; late events retained. H1/H2 not prerequisites for each other.

Online methods see only completed four-sector rates derived from permitted counts, valid masks/timestamps, delivered histories, fixed future probing plans, prior fitted parameters and constraints. They never receive truegain, connectivity/voltages, whole-population measurements or paired-sham activity. `replay.py` opens only public.npz/plans.npz; a full causal mutation fixture runs with evaluator/probe files entirely absent. Retrospective oracle/shams enter only the evaluator after all online predictions are sealed. This is causal chronological replay of uninterrupted trajectories, not a live hardware/deadline demonstration.

## Executed cohort and unchanged instrument

Development0–9: fresh noise32 TUNE,33 RESERVED, each STATIC/LOSS (40trajectories); exploratoryUP0–9/noise32 (10); NULL0–2/noise36 (3); WEAK0–2/noise35 (3). Exactly56development trajectories. Confirmation10–14 × noise32/33 × STATIC/LOSS =20, acquired only after committed selection, regardless of development scientific outcome. No100–119 access, seed replacement or unfavorable network exclusion. Main development inference uses reserved33 only, not tuning32. Validation averages two noise repeats within each of five networks. Historical M003 validation knowledge exists, but these new confirmation streams/outcomes were prospectively reserved.

Original Brian2 2.10.1 recurrent1000 E/I LIF, parameters/topology/delays/OU/current dynamics,100us integration,20ms observations and original causal100ms filter unchanged. Same4stimulation channels and20virtual recording channels;100recorded cells (80E/20I) disjoint from200stimulated E cells. Models use original four filtered observed E outputs. All76 parameter/membership hashes match historical networks. Root20261018; parameter roles0–3 replicate0; OUrole4 absolute1s blocks, spike/action-independent consumption; actionrole5 blocks40/41/42.

All primary runs advance continuously0–79s from fresh engines. Zero0–15s; two8s balanced16-vector probing cycles15–31; onecycle31–39; fivecycles39–79.500ms slots contain100ms zero guard and400ms desired hold; original ramp gives valid delivered actions. Currents0–120pA/channel, total<=240pA, slew<=30pA/channel/20ms. Requested/delivered schedules agree exactly; no violation/fallback. Probing never depends on models or alarms. Nominal model charge=50×sum(u*.02)pC; effective gain belongs to evaluator, not energy/hardware-safety inference.

STATICg1; LOSSg1→.6 at59s; exploratoryUPg1→1.4 at59s; NULLg0 throughout with normal commands; WEAKzero commands withg1→.6. The change is actuator efficacy, not synaptic plasticity. Gain has no algorithm-accessible field.

Checkpoints saved54/64/74s without restoration during primary acquisition. Only after79s does evaluator replay1s active and legal rampdown-sham branches from each corresponding origin. Actual prior current ramps down30pA/channel/tick; sham is not illegal instantaneous zero. Active replay exactly equals primary continuation. All paired noise/checkpoint integrity checks passed. Groundtruth is **continuation minus rampdown from a common history**, not a reset-to-baseline response. Primary online inputs never come from those branches.

Total76×79=6004uninterrupted simulated seconds plus456retrospective replay seconds =**6460simulated seconds**;228origin pairs/456branches. No extra scientific neural trajectories beyond the fixed cohort. Software fixtures use synthetic/replayed observations separately.

## Models, correspondence and causal update order

FIR reference is M003.1's observation-only selected form: q10, inputs current through9previous20ms bins, inputSD floor1pA, output centering, intercept, ridge mean-loss penalty.1, intercept unpenalized;164coefficients. M003.2's .01/RMS/direct-effect fit required paired training labels and cannot initialize an online algorithm; its results remain unchanged. All new coefficients use permitted absolute recorded observations without sham labels.

Provisional fit targets790:1550 ([15.8,31)s),760rows. Eight31–39s prospective1s calibration residuals give fixed output-wise empirical95% widths and scalar residualSD floor.1Hz. At39s final common initialization refits790:1950 ([15.8,39)s),1160rows. All methods receive identical24s probing prefix; the first.8s is a frozen fitting warmup. Means/scales/output center remain fixed after39s. Transferring residuals from the shorter-prefix provisional model is explicitly descriptive, not certified uncertainty.

With x=[u_k,...,u_{k−9}], z=[1,(x−mu)/scale], targetv=r−mean(r):

\[
 A_0=Z^TZ+n(.1)\operatorname{diag}(0,1,\ldots,1),\quad
 \Theta_0=A_0^{-1}Z^TV,\quad P_0=A_0^{-1}.
\]

FROZEN holdsTheta0. SLIDING refits the last250/500 eligible samples every50completed observations (5/10s window, once/sec), same fixed normalization/penalty. RLS updates every20ms completed observation:

\[
 K=Pz/(\rho+z^TPz),\quad
 \Theta^+=\Theta+K(v-z^T\Theta),\quad
 P^+=(P-Kz^TP)/\rho.
\]

Rho grid .995/.999; symmetry enforced. Independent discounted normal equations A+=rhoA+zzT, H+=rhoH+zvT verify correspondence. Initial ridge information is discounted: this is not an unchanged regularizer at every RLS update. Intercept adapts, so absolute-rate gains alone do not prove kernel identification.

At origins39..78s all methods forecast the same next50prescribed actions before future observations; parameters fixed within each1s forecast. Separately, each20ms next-step prediction precedes its completed observation, then models update. Each adaptive method receives2000online observations; RLS performs2000parameter updates; each sliding method accumulates2000samples and refits40times. FROZEN receives the same stream but never refits. No update reset at59 or at detector alarms. Missing/delayed/nonfinite rows are explicitly skipped; duplicate/future timestamps reject. Recorded numerical failure freezes that method's last valid state and prevents complete qualification. Base experiment had zero skips/failures/freezes.

ARX(p4,q4,.1),132coefficients, frozen after39s, is secondary conditional-rate benchmark using only completed histories. SHUFFLED FIR rolls fitting feature rows250bins while targets remain fixed, then uses correct planned inputs. ORACLE is evaluator-only final FIR with lag-specific effective inputs u(t)*trueg(t) and fitted zero-input intercept. It has gain privilege, not future neural observations; nonlinear neural dynamics mean it is not an exact error ceiling. All candidate/source/configuration/coefficient/prediction records preserved.

CUSUM uses frozen-FIR1s residual e=mean(predicted−observed), not adaptive residuals. S=max(0,S+e/sigma−nu), armed only if completed1s mean total delivered current>=30pA. Threshold emits completed-time alarm, resetsS and uses5s refractory; accumulator can grow during refractory. No alarm changes stimulation or estimation. Tuning8registered(nu,h) configurations, and4adaptive candidates, uses only developmentnoise32 STATIC/LOSS. No reserved/validation tuning.

## Selection and primary adaptation results

Tuning selected **RLSrho.999** and **CUSUMnu.5,h5**. Faster candidates had lower changed-gain error but failed stationary/pre-change guardrails: tuning stationary relative harm SW25096.44%,SW50021.27%,RLS99524.21%,RLS999.085%. This is not evidence all adaptation is superior. The same tradeoff persists in reserved/validation results.

| Model | Development post-loss MSE | Development stationary MSE | Validation post-loss MSE | Validation stationary MSE |
|---|---:|---:|---:|---:|
|FROZEN|.429643|.175226|.391978|.199129|
|SW250|.347987|.303755|.366016|.353966|
|SW500|.258512|.207516|.291050|.241299|
|RLS995|.251796|.201060|.284615|.246438|
|**RLS999**|**.295067**|**.168614**|**.297512**|**.197140**|
|SHUFFLED|.507127|.425452|.455503|.438265|
|ARX|.393753|.170723|.355321|.189389|
|ORACLE|.178825|.175226|.196805|.199129|

UnitsHz²; primary MSE is squared error of each1s four-sector mean forecast, averaged over20post-change origins then noise within network then networks. No time bins/noise repeats count as independent networks.

Reserved development: mean absolute benefit **.134576713Hz²**,95%CI **[.107567567,.162736270]**; mean paired relative benefit **30.6394%**,CI[27.2906%,33.9418%];10/10positive. Stationary mean relative harm **−3.7557%**,CI[−8.6903%,.6446%]; pre-changeharm−2.7785%. Every H1 guard passes.

Validation: mean absolute benefit **.094466094Hz²**,95%CI **[.075678354,.108271845]**; mean paired relative benefit **24.0581%**,CI[20.9451%,27.0935%];5/5positive. Stationaryharm **−.8714%**,CI[−3.5307%,1.7349%]; pre-changeharm−1.5562%. Every confirmation guard passes. Relative benefits average within-network ratios, not ratio of pooled means; no denominator floor used.

## Every primary network and detection outcome

Validation entries average two noise repeats; development reserved entries use noise33. Full per-trial/model/origin/sector evidence is preserved in CSV/NPZ; table rounds only for display.

|Network|Frozen post MSE|RLS999 post MSE|Benefit Hz²|Detection by10s|Mean delay s|Stationary alarms/min|
|---:|---:|---:|---:|---:|---:|---:|
|0|.435426|.273059|.162367|1|3|1.5|
|1|.523943|.321169|.202773|1|3|0|
|2|.369360|.286503|.082856|1|2|0|
|3|.531700|.344891|.186808|1|4|0|
|4|.551148|.358435|.192712|1|3|1.5|
|5|.340506|.250020|.090486|1|3|0|
|6|.390974|.284880|.106094|1|1|1.5|
|7|.446032|.324999|.121032|1|3|0|
|8|.371353|.276484|.094869|1|5|1.5|
|9|.335992|.230224|.105768|0|11|0|
|10|.291047|.233882|.057166|1|4|0|
|11|.470413|.374450|.095963|1|6|0|
|12|.444335|.333110|.111225|1|4.5|0|
|13|.382040|.284995|.097045|1|3.5|.75|
|14|.372056|.261124|.110932|1|4|0|

H2 development timely sensitivity **9/10=.90**, empirical networkCI[.70,1]; median delay3s; stationary **.60false alarms/min**,CI[.15,1.05]. Validation timely sensitivity **10/10=1.0** across five networks, median network-mean delay4s; stationary **.15/min**,CI[0,.45]. Paired sensitivity-minus-stationary10s-window probabilityCI[.70,1] in each cohort. All H2 gates pass. Stationary matched-window probabilities0development,.10validation.

All loss events were detected within20s; network9's11s detection was late, not replaced/excluded. One-sided detector emits repeats after a persistent shift: development loss trials40totalalarms including3pre-changefalsealarms, eventprecision10/40=.25; validation33alarms, no pre-changefalsealarms, precision10/33=.303. Stationary totals4alarms/400s and1/400s respectively. The pass therefore qualifies first residual-shift detection under the tested probing regime, **not a deduplicated one-alarm-per-event monitor or diagnosis of actuator loss specifically**.

Only10reserved development events and10validation events were observed. Validation has five independent networks, not ten. Its bootstrap sensitivityCI[1,1] degenerates because all observed network means equal1; it is not a calibrated population guarantee of perfect sensitivity. No pooled15network gate or bin-level pseudo-replication.

## Causal contrasts, calibration, recovery and ordinary prediction

Evaluator-only post-loss continuation-minus-rampdown MSE (origins64/74): development FROZEN.213159, RLS999.136675, ARX.211470, ORACLE.078584, SHUFFLED.512120Hz². RLS benefit **.076484**, network95%CI[.039973,.117893]. Validation FROZEN.124048, RLS999.095359, ARX.120938, ORACLE.111068, SHUFFLED.436942; benefit **.028689**,CI **[−.003894,.072495]**. Thus validation evidence for improved **causal intervention-effect prediction is inconclusive**, despite primary rate-prediction H1 passing. No secondary criterion was retrofitted. The approximate oracle need not dominate every contrast.

Ordinary20ms post-loss MSE: development FROZEN1.586803,RLS9991.331243,ARX.753525Hz²; validation1.505171,1.300713,.751791. Frozen ARX is much better at conditional short-horizon prediction, while selected RLS is better at the tested1s prospective mean. Do not generalize RLS superiority across horizons/information sets.

Post-loss signed mean-rate bias FROZEN→RLS: development .4653→.2976Hz, validation .3972→.2674Hz. MAE .5377→.4317Hz and .5061→.4397Hz. Nominal95% empirical interval coverage improves71.38→80.38% and74.88→82.88%, still substantially under nominal. Same fixed widths for all adaptive forecasts (mean halfwidth .7631/.7939Hz); no widening to manufacture recovery. Stationary coverage is about89%, already undercovered with only eight prequential calibration blocks and transferred provisional-model intervals. These are descriptive, not certified/conformal intervals.

The prespecified sustained-recovery diagnostic (five consecutive1s blocks with scalar absolute bias<=.2Hz and no worse mean MSE than frozen) succeeds only1/10development and0/10validation loss trials; censored median20s in both. **Prediction improved, but complete recovery of calibration was not demonstrated.**

End79s mean kernel-scale proxy .6396development/.5970validation versus trueg.6; mean fitted zero-input baseline change−.0280/−.0257Hz. This suggests input-kernel adjustment, but the projection is not an identified physical-gain estimator or mechanism proof. Bias-only/kernel-only ablations were not included. Complete norms, baselines, proxy traces, actualgain evaluator labels and counts are preserved.

## Negative controls and exploratory schedule

- Stationary trajectories receive identical algorithms/probing. SW250,SW500 andRLS995 fail stationary guards despite changed-gain point gains; retained, not relabeled successful. SelectedRLS999 has no substantial mean stationary loss.
- Input-history shuffling worsens primary and paired-effect predictions. Models do not learn from shuffled confirmation labels or select another alignment after results.
- NULL: all active/sham spikes/counts/rates exactlyequal with physicalg0; no detectoralarms in3trials. Frozen/RLS false-response RMS .1550/.1214Hz across probes reflects finite calibration noise, not actual causal response. Normal commands still arm detector91.7% of blocks, so quietness is not solely suppressed arming.
- WEAK: zero inputs, FIR rank1, undefined gain-scale proxy, zero paired/predicted intervention contrasts. Detector unarmed100%, no alarms despite hiddengainloss; this is **unidentifiability**, not successful efficacy detection. Ordinary MSE FROZEN.169362,RLS.171305; no adaptation superiority claim.
- ExploratoryUP: no post-stepalarms in10trials (expected one-sided sign limitation),2pre-changefalsealarms. Post-rate MSE FROZEN.398691,RLS.282442; descriptive only, not a gate/rescue or plasticity result.
- Post hoc descriptive event-level grouping uses the preregistered1s amplitude strata (no gate/threshold change): development timely1/2low<60pA,3/3middle60–120,5/5high>=120; validation2/2,4/4,4/4. Mean delays7/2.67/3.2s and4.5/3.5/5.25s. Small observational subgroups with different later sequences, not randomized amplitude-effect inference. Block-wise residual/arming/alarm data retained. Current>=30 is presence-of-excitation gating, not a proof of persistent identifiability in arbitrary sequences.
- Future-observation mutation at66s leaves all28earlier rolling origins,1351next-step predictions/model and earlier states/detectorstatistics exactlyunchanged. Missing/delayed/NaN/duplicate/future inputs and numerical instability tested explicitly; no zero-imputation or silent model replacement.

## Engineering, verification and measured cost

Added thin `online_identify.py` and `online_experiment.py`, nine analytical/causality tests, replay/selection/evaluator/audit/reproduction/figure scripts. Existing package exports/dependencies/CI unchanged; test discovery covers additions. No universal plugin framework/frontend. Pinned environment recreated in/tmp because earlier temporary environment was absent; existing Python3.14 repository .venv untouched. Python3.12.15/Brian2 2.10.1/NumPy2.5.4/pytest9.1.1/Matplotlib3.10.8, macOSarm64; full environment.json. pip check passes. All **92tests passed**,25existing deprecationwarnings,30.00s; historical83unchanged. Initial83-test and7-test runs retained.

Independent equations verified76trajectories/532observation archives,304initialfits,12160weighted-batch/sliding coefficient checkpoints,1064000four-output rolling vectors,790400next-step vectors (all frozen/sliding/ARX; sampled RLS interiors), all CUSUM candidates,40matched future-change prefixes, exact active replays, noise/seed/parameter/membership/receipt constraints and all update counts. An additional seed/membership audit confirms36distinct network/noise identities,79absolute OU blocks per primary trajectory and9120channel-to-population count equalities. Numerical RLS equivalence uses discounted information normal equations, not the estimator's inverse-update code. Independent aggregation verifies24320rolling,1824effect,3496secondary-window and18696coefficient rows, development-only selection, committed selection before validation, bootstrap/gates. This is separate analytical implementation in-session, **not external investigator, alternate simulator or biological replication**.

Every adaptive method receives2000online samples, withzero base-case skips/failures/freezes. Full-rank FIR design41 in all normally probed cases, rank1WEAK; initial penalized information condition<=92.52, ARX radius<=.856. Parameter snapshots each1s and initial/final RLS information, complete public observations/predictions/counts/latencies reconstruct intermediate updates; not every covariance was serialized. A repeated complete online replay exactly matches initialization and all12non-timing arrays. Every actual neural active probe reproduces primary continuation exactly.

Deterministic reanalysis reproduces98scientific CSV/JSON/NPZ/PNG/SVG artifacts (only measured analysis runtime excluded). Oracle paths were serialized afterward as a clearly labeled derived evaluator archive, independently matching3040already-scored rolling metrics; no neural rerun/refit/selection change. All original outputs remain. Curated copies and complete SHA inventory are preserved.

Actual acquisition: development4760simseconds/**1272.448wallseconds**, validation1700/**888.680wallseconds**; total6460simseconds/2161.128wallseconds (36.02min across3workers), not an isolated single-thread benchmark. Initialization ranges.0131–.1480s and.0249–.0499s. Peak recorded workerRSS1178599424bytes development,1326202880bytes validation (~1.235GiB); simultaneous aggregate not measured. Development replay/selection37.035/.262s; validation replay14.578s; evaluator9.255s; initial independent development12.175s, extended13.675s; validation4.830s subprocess; independent scientific aggregation5.835s; figures1.858s. All declared caps respected.

SelectedRLS999 measured1s-forecast median22.583µs,p9526.875µs,max1801.625µs; per-observation update median35.5µs,p9548.458µs, **max91657.542µs**. Three/152000updates exceeded20ms. ARX1s-forecast median669.292µs,p95983.712µs,max43837.208µs (one/3040over20ms). Other methods/timings fully archived. Wall-clock outliers were not cause-isolated. **No hard20ms real-time qualification**; virtual causal replay does not backdate computation. VECLIB/OMP/OPENBLAS limits requested1; actual Accelerate threading unverified. Costs include actual concurrent local workload/cache effects, not standardized backend guarantees. Disk/source inventory in finalmanifest.

## Decisions, limitations and next falsifiable experiment

ExecutionPASS with transparent timing clarification; H1PASS for **prospective1s mean-rate prediction under continued externally prescribed probing**; H2PASS for a **one-sided residual-shift flag under gainloss**. Use selectedslowRLS for that tested drift-prediction regime; retain frozenFIR as stationary/reference and ARX as strong20ms conditional benchmark. Do not claim every adaptive method helps, full calibration recovery, confirmed validation intervention-effect compensation, physicalgain identification, controllability or biological relevance.

Limits in priority order: validationpaired-effectCI crosseszero; sustained recovery/interval coverage poor; repeatedalarms loweventprecision; onlyfiveconfirmationnetworks/twentysecondpostwindow; gainloss is one known simulatedcause, not specific diagnostic identification; insufficient excitation fundamentally unidentifiable; kernel/intercept mechanism not isolated; finite excitation/model/forgetting grids and one perturbationamplitude; causal offline replay is not live real-time hardware. No historical V0 failure is reinterpreted.

Next falsifiable experiment: preregister bias-only versus input-kernel-only versus fullRLS updates on fresh observation-based calibration/streams, retaining paired evaluator-only contrasts. Test whether kernel updating is necessary for replicated intervention-effect improvement beyond adapting the baseline. Freeze meaningful contrast/stationarity/uncertainty gates before acquisition. This is proposed only; no controller or follow-on study started.

M004 stops after review/report/commit. No merge, push, controller, target engineering, plasticity, hardware or locked-network experiment.
