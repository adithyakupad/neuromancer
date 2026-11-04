"""Verify the installed wheel, not PYTHONPATH source imports."""
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path

root = Path(__file__).resolve().parents[5]
results = {}
for name in ("control", "identify", "online_identify", "predictive"):
    module = importlib.import_module("neuromancer." + name)
    installed = Path(module.__file__).resolve()
    source = root / "src" / "neuromancer" / (name + ".py")
    assert "site-packages" in installed.parts, installed
    assert installed.read_bytes() == source.read_bytes(), name
    results[name] = dict(path=str(installed), sha256=hashlib.sha256(installed.read_bytes()).hexdigest())
assert importlib.metadata.version("neuromancer") == "1.0.0"
Path(__file__).with_name("installed_imports.json").write_text(json.dumps(results, indent=2) + "\n")
print("PASS: installed1.0.0 wheel matches all four readability sources")
