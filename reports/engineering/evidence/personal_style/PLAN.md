# Personal-style refactor: prospective engineering acceptance

2026-11-04. No new scientific acquisition, model selection or outcome analysis.
Four candidate production files only: control.py, identify.py,
online_identify.py, predictive.py. Leave numerical engine, observation, planner,
supervisor, clocks, runners, evaluation and all historical snapshots unchanged.
First qualify the separate M009 release backport on Linux/macOS.

Before production edits, preserve source blobs in Git and source SHA256s,
and capture exact synthetic outputs plus one development-only 1s neural replay.
The probe's first unprivileged dry run failed at the fail-closed boot-identity
check; retain that failed attempt, do not bypass the native clock.

Required equality: exact dtype, shape and array bytes; exact JSON records.
Includes FIR/AR/ARX coefficients/forecasts/normalization, online RLS information
and coefficient states, PI states, commands, all 625 candidate scores and
predictions, selected actions and public observations/full spike events.
Exclude real elapsed time and source identity from numerical comparisons;
record both separately. No operation reassociation, changed constraints,
tie rules, tolerances, clock calls, exception policy, or algorithm changes.

Formatting must preserve AST before local-name/comment changes. Limit manual
changes to naming intermediate scientific quantities and direct state setup.
Each substantive stage runs relevant historical tests and exact golden probe.

Timing: nine recorded repeats per fixture, no exclusions; first sample is
reported as cold/first call, remaining eight as warm. Final paired ABBA runs
against a separate original-source tree, three cycles, when practical.
Material regression thresholds fixed before edits: >10% paired median or
>20% paired p95 wall-time regression for affected workloads requires rejection
or separate review. Native process peak RSS must not increase >10% and must
remain inside existing supported resources. Report noise and finite precision;
do not equate statistical uncertainty with proof of no regression. Deadlines
remain 250ms in production; planner benchmark allows 10s solely to measure
cost, with unchanged candidate/score computation. Golden probes use a fixed
injected clock; real deadline failure behavior remains independently tested.

Resource bounds: individual probe240s, full qualification1200s, one worker;
no unrestricted sweep. Requested BLAS thread environment is not proof of
actual thread behavior. Keep Python and scientific dependencies pinned.

Final gates: full historical tests, exact replay, source-preservation audit,
committed-evidence numerical/figure reproduction, wheel/import and hosted
Linux/macOS checks on resulting source. No merge, tag or publication.
Readability evidence: reduced multi-statement lines, expanded decisions,
named math intermediates, before/after examples and function guide. These
proxies cannot certify the user's independent understanding or authorship.
