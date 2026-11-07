The first focused pytest command ran with restricted macOS system
calls. The two PID publication cases failed at the boot identity
check before launching a worker. Both passed under the qualified host
clock. The fail-closed clock check stayed unchanged.

The superseded source used a repository-namespace import in the new
test. Module-invoked pytest passed, while plain pytest collection
failed. The corrected test loads the verifier from the repository
file by path. The plain pytest collection check then found all three
cases. The official full suite was run on the corrected source.

The first SDK environment pip check inherited the repository source
path and picked up core project metadata. It reported missing Brian2
and a SciPy mismatch before any SDK run began. Checking the SDK in its
isolated environment passed. The subsequent local SDK matrix ran once
on the superseded integration revision, before the pytest-only
follow-up. The original SDK matrix was subsequently hosted on the
corrected exact head.
