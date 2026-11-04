"""Losslessly archive only new untracked M010 pytest trees; retain originals."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

root = Path("reports/engineering/evidence/m010").resolve()
retained = Path("/tmp/neuromancer-m010-retained-test-trees")
retained.mkdir(exist_ok=False)
records = []
for phase in ("focused", "full"):
    for name in ("test_tmp", "test_artifacts"):
        source = root / phase / name
        assert source.is_dir() and source.is_relative_to(root)
        assert not subprocess.check_output(["git", "ls-files", str(source)])
        inventory = {}
        for path in [source, *source.rglob("*")]:
            relative = str(path.relative_to(source.parent))
            if path.is_symlink():
                inventory[relative] = dict(kind="link", target=os.readlink(path))
            elif path.is_file():
                inventory[relative] = dict(kind="file", sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            else:
                inventory[relative] = dict(kind="directory")
        archive = source.with_suffix(".tar.gz")
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
        target = retained / phase / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, target)
        records.append(dict(original=str(source), archive=str(archive.relative_to(root)),
                            archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                            entries=len(inventory), recovered_bytes_verified=True,
                            retained_original=str(target), inventory=inventory))
(root / "pytest_archive_preservation.json").write_text(json.dumps(records, indent=2) + "\n")
print("PASS: all four new pytest trees losslessly archived; original trees retained")
