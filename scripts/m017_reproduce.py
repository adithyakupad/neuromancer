"""Reproduce M013/M014 summaries from copies and check the V2 historical archive."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MANIFEST = Path("reports/engineering/evidence/m017/base_preservation.json")
MANIFEST_SHA256 = "f88c41d51355e115863fd1a12dee6901aa4034ac7bf68f86c0c64e622e1719b1"
# M026 and final core-release fixture authorization use exact file hashes, never path-wide exemptions.
AUTHORIZED_REPLACEMENTS = {
    "scripts/m016_run.py": (
        "781893b0e301d2b858b185b19db4b322451c0d8ed58255a356dda5ad4a826a1b",
        "03661773740d1b0fcb83fa8eddc1496f06c5fd432f72119670e84f6ebae3dad6",
    ),
    "scripts/m016_verify.py": (
        "9d2e26072c913e47695cdf54146a73d670bde94d6c162e329120273d978c41f2",
        "46cb116e269c25a0ec89c60db12c69c519ca756ee28a2e835dc8fb57fb91ee3d",
    ),
    "tests/supervisor_worker.py": (
        "c19982062ba119b1a86db187d62c2ee9b1f25725398a526a36e60072250b2fef",
        "2e9a482da8a7819926531119fc9c73b2c4106f9e44f8368858bbddd3ac722471",
    ),
    "tests/test_suspend_clock.py": (
        "e6ac4422f251c6de7602321c7cc4dc01bffd19a00ff76f8f0e7bcb1bd46eca86",
        "1edd4e2a5db202b4626371b2127c9f5b801b534aba8fdea27c711e18c5461128",
    ),
}


def verify_history():
    manifest_bytes = MANIFEST.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise AssertionError("Protected baseline manifest differs")
    protected = json.loads(manifest_bytes)["protected_sha256"]
    for name, (original, replacement) in AUTHORIZED_REPLACEMENTS.items():
        if protected.get(name) != original:
            raise AssertionError(f"Replacement does not match baseline: {name}")
        protected[name] = replacement
    for name, expected in protected.items():
        path = Path(name)
        if name in AUTHORIZED_REPLACEMENTS and (path.is_symlink() or not path.is_file()):
            raise AssertionError(f"Authorized replacement must be a regular file: {name}")
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise AssertionError(f"Protected baseline path differs: {name}")
    return len(protected)


def main(output):
    result = {"audited_paths": verify_history(), "archives": {}}
    for stage, folder, script in (
        ("m013", "pilot_typed", "m013_analyze.py"),
        ("m014", "pilot", "m014_analyze.py"),
    ):
        source = Path("reports/research/evidence") / stage / folder
        scratch = output / stage
        shutil.copytree(source, scratch)
        subprocess.run([sys.executable, f"scripts/{script}", str(scratch)], check=True)
        original = json.loads((source / "independent_analysis.json").read_text())
        reproduced = json.loads((scratch / "independent_analysis.json").read_text())
        assert original == reproduced, stage
        result["archives"][stage] = reproduced
    (output / "reproduction.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
