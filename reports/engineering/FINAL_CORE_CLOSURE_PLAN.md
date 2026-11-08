# Final core closure finite qualification plan

Base is current remote main db4485613cba8128ee643159b25ef29523ca6c95.
PR #5 was already merged at a5ebbad4 before this campaign. Tags and
public releases were empty at reconnaissance. Version stays
2.0.0rc1. No scientific or production algorithm changes are planned.

The original failure at 42334001244 recorded DEADLINE_EXCEEDED with
terminal NOT_STARTED, state CREATED and no worker PID. A fixed-time
clock injection occurred before launch. No worker checkpoint could
exist. The supervisor's contract permits this fail-closed result.
The later merged fixture fix gates post-checkpoint suspend scenarios
on actual parent/descendant checkpoint files. This campaign adds
deterministic tests against the actual injection function. The
original deadline, injected values, cleanup and assertions stay fixed.

Perform one local full suite, one golden replay, one V1 canonical
reproduction and archived M013–M016 checks, each supervised with
the existing 180/240 s limits. Use a clean wheel install with 120 s
CLI budget. No physical suspend, SDK optimization, locked cohorts
or new scientific acquisition.

Push one final hardening source. Existing core/substrate/SDK
workflows run unchanged. A closure workflow runs one job per host.
Each host runs three prespecified rounds of the five original real
resume cases, keeping their original budgets and independent watchdog.
Also run exact golden and archive reproduction with existing scripts
and tolerances, in separate always-run steps so each outcome is
recorded. The job cap is 25 minutes. No reruns on unfavorable outcomes.

The publication failure at 42428618054 includes a Linux M014 exact
prediction discrepancy of 4.99600361e-16. Its tolerance remains zero.
The existing M013 portability allowance is not expanded. Exact
replay failure remains a mandatory blocker and cannot be replaced by
a comparison using relaxed tolerances. If any mandatory gate fails,
preserve candidate, logs and release HOLD. No merge/tag/publication
will occur in that case. Reports are archived separately from the
exact source being tested.
