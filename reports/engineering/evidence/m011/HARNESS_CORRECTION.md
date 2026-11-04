# Prospective harness-only completion, no candidate changes

The immutable86ad99f6V1source passed200tests/25warnings, exact91-array/JSON and
four-table/four-figure reproduction. Qualification harness stage2pip reported
already-installed because inherited PYTHONPATH=src exposed build egg-info; actual
site-packages/CLI were absent. Stage3/4correctly failed. This did not establish
a broken wheel: no noneditable installation had occurred. Clear PYTHONPATH for
pip installation, then verify actual installed files and CLI.

All ten extra original lifecycle assertions passed, but their pytest invocations
failed teardown because the harness reused the full-suite artifact root and the
same node hash. Retained per-repeat XML/tmp/returned.json and errors explicitly
show FileExistsError copying to an existing artifact directory. This is not the
write_failure deadline assertion. Keep the first bank unchanged. Set a fresh
artifact root per repeat and run ONE corrected ten-case bank, fixed before
execution, no replacement seeds or candidate-source edits. This is completion
of invalid harness execution, not rerun-until-green of a V1 lifecycle failure.

Only actual install/import/smoke and corrected repeat bank are rerun. Reuse the
same original1200sdeadline/clock while still live; no deadline extension. The
original failed harness status remains. If a real original test fails or budget/
cleanup/clock integrity fails, retain V1HOLD. Scientific/historical outputs are
not rerun or rewritten. Existing source86ad99f6remains unchanged and fresh
hosted checks on release/m011-v1-isolated remain independently mandatory.
