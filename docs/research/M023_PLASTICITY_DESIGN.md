# M023 reward-modulation mechanism design

M013 remains inconclusive. Across networks 13000 and 13001, ordinary
eligibility-based STDP scored 62.50% and 68.75%, versus 56.25% on both
under signed decoder reward. The matched pilot had two networks.
These differences cannot identify reward noise, cold start or credit
timing.

## Two hypotheses

1. **Reward alignment.** The cold-start decoder's signed reward
   suppresses or redirects useful eligibility updates. For an edge,
   mean(R E) = mean(R) mean(E) + covariance(R, E), using the population
   minibatch covariance. Distinguish low signed mean reward from
   reward-to-trial alignment by replaying the same eligibility and
   reward magnitudes with exactly permuted labels. Compare online
   training rewards with rewards from a readout frozen after a
   development-only decoder warm-up. Match training trajectories and
   inspect signed covariance before any nonlinear weight clipping.
2. **Eligibility timing.** Rewards miss the useful interval as
   eligibility decays between the last paired spike and the decoder
   decision. On the identical pulse/spike history compare reward
   application at the original timestamp and an earlier legal decoder
   timestamp. Match reward signs and magnitudes. A timestamp shift
   cannot use a decoder output that did not yet exist. A separate
   same-timestamp longer-decay arm distinguishes delay from scale.
   Measure positive/negative mass, edge-norm, clipping and the ratio
   of causal to background eligibility. Include a magnitude-matched
   unmodulated arm to detect a mere learning-rate effect.

## Executable first check

The deterministic fixture in `tools/recover_models.py` exhaustively
enumerates four signed-reward assignments to a fixed four-entry
eligibility vector, then reports the signed moment and exponential
attenuation for one and two time constants. This tests arithmetic and
non-identifiability. It supplies no evidence that either mechanism
caused the M013 differences.

## Conditional study

Fresh development IDs 23100–23105. Fit/warm-up, reward-training and
readout-probe blocks are disjoint, with each realization shared across
arms, randomized paired stimuli and matching OU innovation roles.
Reserve separate IDs beginning at 23200 only after precision and
runtime qualification. Primary mechanism endpoint is the network-level
difference in signed reward–eligibility alignment against its exact
within-minibatch permutation reference. The downstream held-out
contrast is reward modulation versus both unmodulated and shuffled
reward, alongside frozen recurrence. Report network-level intervals
and accuracy separately from update diagnostics. No confirmation
count is asserted without a development variance estimate and
independent precision review. Start with one bounded benchmark before
acquisition and reject if the forecast cannot fit the 600 s development
cap with 25% headroom. Historical or previously used networks provide
context only.
