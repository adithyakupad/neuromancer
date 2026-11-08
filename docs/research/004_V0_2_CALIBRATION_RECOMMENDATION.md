# V0.2 recommendation after prospective M002.3 confirmation

**HOLD — scientific qualification failed,0/10 networks; required8/10.** This is an append-only recommendation. [V0.1](002_V0_PROTOCOL.md) and [conditional V0.2](003_V0_2_PROTOCOL_PROPOSAL.md) remain unchanged. M002/M002.1's +4Hz failure and M002.2's slow7/10 screen remain their original results. All evidence is simulated, on development networks0–9 only. [Complete report](../../reports/M002_3_CALIBRATION.md), [frozen protocol](../../reports/evidence/m002_3/PREREGISTRATION.md).

## What was confirmed

Exactly50 fresh prefixes (noise8–12),51s each, and400 paired6s branches completed under the unchanged model/interface. Calibration used only completed observations and delivered commands. Targets were prospectively fixed from the actual preceding-zero h(q) map: R*=.6h120, L=b+.1R*, H=b+.9R*. All10 network mean spans exceed1Hz (range1.0404–1.5240Hz) and twice standalone1s noise. Baseline/numerical/timing/replay/constraint checks pass. The software/evidence execution gate passes, with54 tests and independent numerical recomputation.

These findings do not validate prospective control. Only7/10 networks have all five calibration maps valid. Noise-dependent local reversals occurred at(network1,noise11), (2,12), (6,8); no smoothing or replacement was applied. Reduced-efficacy lower-confidence headroom passes7/10, failing networks2,5,6. Their positive mean headroom margins do not resolve the frozen confidence requirement. Even before realization, only6/10 pass the intersection of calibration, headroom and the other prerequisite components.

## Blind lookup versus known-gain reachability

M002.3 explicitly disallowed true-gain input to both calibration and lookup. Its preregistration therefore used q=h^{-1}(target−b), identically at g=1/.6. It did **not** execute the conditional proposal's evaluator-known-gain q=q_eff/g assay or a post-loss recalibration. Do not present those unexecuted assays as prospective successes.

Every network fails the reduced-gain high-target realization gate. Among the seven fully valid-map networks the mean normalized high-target errors range.4093–.5165, versus<=.25 required. Including the three invalid-map zero-current fallbacks, the full-cohort mean is.5000 (descriptive network-bootstrap95% interval.4607–.5449). Invalid fallback errors are actual outcomes, not valid lookup estimates or excluded trials. Maximum C120 still produces a positive late paired response: cohort2.6641Hz at g=1 and1.6403Hz at g=.6. This distinguishes blind underdelivery from proof of no possible actuation authority. It does not establish an entire reachable interval or a successful gain-blind policy.

A fixed open-loop calibration cannot detect an unobserved gain change. Better precision alone would not make it do so. This experiment shows neither feedback failure nor adaptive-controller benefit; those methods were not implemented. The low-target offset is only.125span while error tolerance is.25span, so low-target success alone is weak evidence: an ideal zero-input baseline would pass that component. The nontrivial high/low span remains intact, and the high-target gate decisively fails. Do not tighten or relax these rules retrospectively.

## Recommendation

Keep the controller-evaluation path on HOLD. Do not open validation/test networks, shrink spans, lengthen calibration, repair nonmonotone maps, introduce known-gain compensation under a blind label, or alter neural parameters to rescue this protocol. Do not treat the M002.2 screen as a passed prospective procedure.

Prioritize a separately preregistered **stimulation-response identification** objective using the already qualified causal substrate. A useful next question is whether a fixed-budget observation-only calibration predicts independently scheduled dose-response changes, beyond a no-input prediction, under stationary versus hidden efficacy-loss conditions. A candidate falsifiable gate is at least10% reduction in reserved evoked-response MSE versus the no-input predictor, with the paired network-level95% benefit interval excluding0; failure of either rejects that identification claim. This reuses the original design’s identification-effect threshold and still requires a new complete preregistration. That is a test of intervention identification under partial observations, rather than further target construction. Specify prospective excitation/zero-reference budget, reserved evaluation windows, no-input/shuffled-input controls, independent new noise, network-level precision and falsification thresholds before execution. No new experiment or identification algorithm is authorized by this recommendation.

A separately reviewed substrate redesign remains an option only with an explicit modeling/scientific motivation and new versioned protocol. This result supplies no reason to increase currents, weaken inhibition or record stimulated cells merely to obtain success. A future gain-aware assay or allowed recalibration must be labeled as a different information/budget condition and cannot rehabilitate the present blind qualification.

Stop after M002.3. No ARX,PI,MPC,RLS,RL,plasticity or hardware integration follows automatically.
