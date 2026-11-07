# Prospective CI runner clarification, 2026-11-04

The original exact-source run41887694865 at4e180c35 never acquired its macOS arm64
runner. GitHub annotations explicitly report hosted-runner acquisition failure and
arm64 capacity constraints. Linux and legacy checks passed. Attempt1 is preserved;
attempt2 retries the same source, without removing that failure from history.

Use the documented standard macos-15-intel runner for the macOS qualification job.
This changes the CI execution architecture only, not package/source/dependencies,
test selection, assertions, deadlines, process fixtures, scientific code or data.
Run all200tests and35process diagnostics plus wheel/pip-check/smoke as before.
Linux must pass on the same new revision. macOS arm64 is tested locally on26.5.2;
this fallback must never be represented as hosted-arm64 qualification.

Authoritative runner labels (accessed2026-11-04):
https://docs.github.com/en/actions/reference/runners/github-hosted-runners
The exact original M008 workflow copy remains recorded at4e180c35 and by the
original backport manifest. This prospective, explicit exception changes only
macos-latest -> macos-15-intel in the active qualification workflow.
No neural acquisition, scientific rule change, test omission or relaxed timeout.
A failed Intel job remains a failure; capacity errors do not constitute a PASS.
