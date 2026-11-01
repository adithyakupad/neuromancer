# Provenance-test repair

Hosted substrate run41344142135 at3fb6f2b passed182tests and failed test_execution_lineage_frozen_before_neural_run because M007 intentionally corrected README. No neural or numerical discrepancy was found.

Preserve the original README from starting revision6420f852 verbatim at docs/history/README_M002_SNAPSHOT.md; verify its SHA256 against the unchanged M002.3 preservation manifest. Modify only that historical README lookup in the test. All other historical source/data hash assertions remain unchanged; no expected digest or frozen scientific artifact changes. Source Git history and M007 before/after manifest preserve the documentation transition. Rerun all183tests locally and hosted; do not skip or weaken the provenance assertion.
