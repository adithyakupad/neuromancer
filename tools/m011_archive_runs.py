"""Losslessly package only new M011 audit trees, retaining originals locally."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

root = Path("reports/engineering/evidence/m011").resolve()
retained = Path("/tmp/neuromancer-m011-retained-audit-trees")
retained.mkdir(exist_ok=False)
records = []
for name in ("v1_qualification", "v1_candidate_42e20"):
    source = root / name
    assert source.is_dir() and source.is_relative_to(root)
    assert not subprocess.check_output(["git", "ls-files", str(source)])
    inventory = {}
    for path in [source, *source.rglob("*")]:
        relative = str(path.relative_to(root))
        if path.is_symlink():
            inventory[relative] = dict(kind="link", target=os.readlink(path))
        elif path.is_file():
            inventory[relative] = dict(kind="file", sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            inventory[relative] = dict(kind="directory")
    archive = root / (name + ".tar.gz")
    assert not archive.exists()
    with tarfile.open(archive, "w:gz", dereference=False) as output:
        output.add(source, arcname=name)
    with tarfile.open(archive) as output:
        members = {member.name: member for member in output}
        assert set(members) == set(inventory)
        for relative, value in inventory.items():
            member = members[relative]
            if value["kind"] == "file":
                assert hashlib.sha256(output.extractfile(member).read()).hexdigest() == value["sha256"]
            elif value["kind"] == "link":
                assert member.issym() and member.linkname == value["target"]
            else:
                assert member.isdir()
    # Keep the top-level decision available without extracting the archive.
    shutil.copy2(source / "status.json", root / (name + "_status.json"))
    shutil.move(source, retained / name)
    records.append(dict(original=str(source), archive=archive.name,
                        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                        recovered_bytes_verified=True, retained_original=str(retained / name),
                        inventory=inventory))
(root / "audit_archive_preservation.json").write_text(json.dumps(records, indent=2) + "\n")
print("PASS: two new audit trees archived, all member bytes verified, originals retained")
