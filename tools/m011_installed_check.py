"""Clean isolated V1 wheel check; run without PYTHONPATH source imports."""
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys
import zipfile

source = Path.cwd()
output = Path(sys.argv[1])
wheel = next((output / "wheel").glob("*.whl"))
assert importlib.metadata.version("neuromancer") == "1.0.0"
hashes = {}
for name in ("_brian", "supervisor", "clocks", "control", "identify", "online_identify", "predictive", "predictive_planner"):
    module = importlib.import_module("neuromancer." + name)
    installed = Path(module.__file__).resolve()
    assert "site-packages" in installed.parts
    expected = source / "src/neuromancer" / f"{name}.py"
    assert installed.read_bytes() == expected.read_bytes(), name
    hashes[name] = dict(path=str(installed), sha256=hashlib.sha256(installed.read_bytes()).hexdigest())
with zipfile.ZipFile(wheel) as archive:
    license_path = next(name for name in archive.namelist() if name.endswith("/licenses/LICENSE"))
    assert archive.read(license_path) == (source / "LICENSE").read_bytes()
    metadata_path = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
    metadata = archive.read(metadata_path).decode()
    assert "Version: 1.0.0\n" in metadata and "License-Expression: MIT\n" in metadata
record = dict(status="PASS", hashes=hashes, wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
              versions={name:importlib.metadata.version(name) for name in
                        ("neuromancer", "numpy", "brian2", "scipy", "pytest")})
(output / "installed_check.json").write_text(json.dumps(record, indent=2) + "\n")
