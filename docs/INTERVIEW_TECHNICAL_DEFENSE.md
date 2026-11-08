# Technical defense guide

Work through the equations and reproduce the tests before presenting the
implementation. These questions are prompts for independent understanding.
Each set moves from definition to reasoning to experimental judgment.

## 1. LIF dynamics

`_brian.py` integrates 1,000 voltages using
(C\dot V = C(V_r-V)/\tau_m + I_E + I_I + I_{background} + \eta + I_{stim}).
Inputs are currents in pA, states are voltage, refractory status and
noise, and outputs are timestamped spike indices. Threshold crossing
resets voltage and enters a refractory window. The 100 µs step and
solver are part of the model. `tests/test_substrate.py` exercises replay.
Questions. What makes the membrane leaky? How do refractory steps
affect repeated spikes? What test separates integration error from a
different neuron model?

## 2. Recurrent E/I synapses

Each edge stores source, destination, signed current jump and delay
as connection vectors. Between arrivals (\dot I=-I/\tau). At arrival
a source spike adds its weight to the target current. Current decay,
spike queues and voltage determine future activity. `_brian.py` and
`tests/test_causal_memory.py` exercise graph and delay preservation.
Questions. What sign enters the inhibitory current? Why does delay
affect replay? How could you distinguish a feedback effect from a
change in inhibition after ablation?

## 3. STDP and eligibility

`plasticity.py` uses E/E pathway vectors. A presynaptic or postsynaptic
event first decays its traces with (e^{-\Delta t/\tau}), then applies
the pair contribution. Eligibility stores a signed contribution for a
later reward. Snapshot restoration must include clock and trace state.
`tests/test_plasticity.py` compares pair updates to independent arithmetic.
Questions. Which ordering potentiates an edge? What changes when
spikes coincide? Which state must be restored to replay a reward?

## 4. Reward credit assignment

For eligibility (E_{ij}) with axes trial and connection, reward
(r_i) gates the update (w_j'=\operatorname{clip}(w_j+
\alpha\operatorname{mean}_i(r_iE_{ij}),0,30)) in pA. Rewards do not
reach the controller observation API. M013 compares frozen,
unmodulated and shuffled controls. `tests/test_plasticity.py` checks
zero reward, bounds and disabled updates.
Questions. How does reward change a pair update? Why is this delayed
credit assignment? Which control tests whether reward modulation
adds value beyond STDP?

## 5. Reservoir computing

The fixed recurrent substrate maps input histories into dynamical
state. `reservoir.py` takes completed count bins and builds 20 final
rates or an 80-entry history. Only the readout is fit. Reset and
independent noise streams define the trial. `tests/test_reservoir.py`
checks dimensions and feature timing.
Questions. Which weights are fitted? Where does the history buffer
store information? How could you test retention when recurrence also
carries the stimulus to the recorder?

## 6. Temporal decoding

`functional_learning.py` fits ridge coefficients by solving
((X^TX+\lambda I)\theta=X^Ty) after fit-only scaling. Rows are trials,
columns are features, and held-out predictions are thresholded for
balanced accuracy. Validation chooses the penalty. `tests/test_functional_learning.py`
checks exposure and label isolation.
Questions. What does balanced accuracy average? Why freeze scaling
before scoring? What does a full-history baseline reveal about a
temporal XOR task?

## 7. FIR and ARX

`identify.py` and `online_identify.py` build lag vectors from causal
four-channel inputs. FIR maps recent stimulus into four observed
sector rates as an intercept plus the sum of lagged input products. ARX adds a sum of lagged rate products. Forecasting advances
with predicted, not future measured, outputs. `tests/test_identify.py`
checks features and recursive forecasts.
Questions. What is a lag? Why does ARX need a stability check? Where
would teacher forcing leak future information?

## 8. RLS

`predictive.py` stores coefficients (41×4) and inverse information
(41×41). For standardized row (z), gain is
(g=Pz/(\rho+z^TPz)). The update adds (g(y-z^T\theta)^T)
and updates (P=(P-gz^TP)/\rho), then symmetrizes it.
Validity gates protect causal updates. `tests/test_predictive.py`
compares against weighted batch normal equations.
Questions. What does forgetting do? Why skip invalid observations?
How would rank deficiency affect adaptation?

## 9. PI and anti-windup

`control.Policy` aggregates completed rates, computes target minus
rate, proposes an integral increment (K_i e\Delta t) and clips it.
It blocks increments that deepen saturation. A separate projection
enforces slew, box and total budget across four currents.
`tests/test_control.py` checks timing and feasible actions.
Questions. What is integral windup? Why keep projection separate?
How would delayed observations alter the safe response?

## 10. MPC

`predictive_planner.py` evaluates 625 candidate action pairs over
100 future bins with a causal four-channel history. It predicts rates,
evaluates tracking error squared plus dose and switching penalties, applies constraints and selects a stable tie
winner. Finite wall time limits the calculation. `tests/test_predictive.py`
checks all candidates against an independent projection and forecast.
Questions. What is the optimization variable? What makes a candidate
feasible? Why can adaptation worsen realized tracking?

## 11. Reproducibility

Network realization and OU innovations use separate seed roles.
State snapshots hold queues, clocks and observation cursors. Scientific
artifacts carry source and data hashes. See `_brian.py`,
`tests/test_substrate.py` and `scripts/m017_probe.py`.
Questions. Which random stream changes across trials? Why does the
Brian RNG flag not restore NumPy innovations? What does exact spike
replay establish about portability?

## 12. Experimental controls

M015 pairs stimulus and sham on identical innovation streams. C0,
disconnected C1 and DAG C2 separate reachability from observable cue
encoding. C2 has an ordered E/I graph with retained signed weights
and delays. See `causal_memory.py` and `tests/test_causal_memory.py`.
Questions. Why use matched sham? Can a reachable recorder carry
negligible signal? What comparator could isolate recurrence-specific
retention?

## 13. Statistical inference

The pilot network is the replication unit. The primary comparison
uses a paired network-level difference and a descriptive t interval
when the cohort has two networks. Balanced accuracy uses per-class
recall before averaging. `scripts/m013_analyze.py` and
`scripts/m014_analyze.py` reconstruct the frozen outcomes.
Questions. What is pseudoreplication? Why is the interval wide?
What precision and controls would justify a new confirmatory cohort?

## 14. Clock domains

`neural_io.FrameClock` uses exact ((f-f_0)\times40) µs at 25 kHz.
A 500-frame bin is half-open and becomes available after its end.
`clocks.py` and `supervisor.Deadline` use suspend-inclusive
OS nanoseconds. `tests/test_neural_io.py` and `tests/test_suspend_clock.py`
check boundaries.
Questions. What happens to an event at the bin endpoint? Why keep
host and device epochs separate? What should happen after an
unprovable clock discontinuity?

## 15. SDK recording and stimulation

`cl_adapter.py` accepts one simulator-only biphasic electrode request
and records acceptance before receipt. Raw frames are int16
(frame, electrode), spike records carry frame and electrode, and HDF5
events are translated from recording-relative time. `scripts/m017_sdk_verify.py`
reconstructs the real SDK ledger.
Questions. How is submission different from commitment? What is
the causal PI update point? Which controls distinguish a designed
response from an analysis artifact?

## 16. Hardware boundary

`cl_adapter` requires a verified installed SDK and literal simulator
identity before open and submit. `neural_io` checks maps, missing
frames, late requests and the fixture pulse. `tests/test_neural_io.py`
tests refusal paths. Physical safety would require separately
authorized devices and evidence.
Questions. Where is hardware refused? Why is pA injection different
from electrode µA? How should an unverified device identity affect
actuation and logging?
