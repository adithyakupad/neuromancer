# V2 reproducibility

The M017 base inventory records all tracked blob identities at M016.
The preservation manifest records physical SHA-256 checks for evidence,
documentation and Python sources. Packaging and workflow changes are
visible in Git. The style review uses an explicit list of eligible
implementation paths. Archived data and hash-qualified M002 sources
are byte-protected. Historical commands that audit an entire original
source tree should be run from a detached checkout of that source.

```sh
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python scripts/reproduce_v1_evidence.py --output /tmp/v2-v1-evidence
PYTHONPATH=src python scripts/m017_reproduce.py /tmp/v2-computation-replay
python scripts/m017_sdk_verify.py reports/engineering/evidence/m016/final_matrix
```

The SDK verifier requires its isolated environment. V1 reproduction
compares original numerical artifacts by byte and checks figure hashes
separately. The V2 engineering probe retains dtype, shape, bytes and
JSON records. Native timing, wall-clock SDK recording metadata and
process identifiers are measured separately.

Use the [quickstart](V2_QUICKSTART.md) for fresh engineering examples.
The SDK environment archive is
[recorded here](../reports/engineering/evidence/m016/sdk_environment.txt).
Source installers and SDK subprocesses use the documented import path.
Reports and raw NPZ/HDF5 artifacts live in the repository, with no
historical scientific acquisition required for routine verification.
