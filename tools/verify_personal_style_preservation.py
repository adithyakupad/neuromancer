"""Check every tracked reference file; allow only four declared source edits."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_revision")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    allowed = {f"src/neuromancer/{name}.py" for name in
               ("control", "identify", "online_identify", "predictive")}
    changed = {}
    count = 0
    tree = subprocess.check_output(["git", "ls-tree", "-rz", args.reference_revision])
    for row in tree.split(b"\0"):
        if not row:
            continue
        metadata, encoded_name = row.split(b"\t", 1)
        name = encoded_name.decode()
        path = Path(name)
        assert path.exists() or path.is_symlink(), name
        data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        count += 1
        if hashlib.sha1(blob).hexdigest() != metadata.split()[2].decode():
            assert name in allowed, f"Unexpected historical change: {name}"
            original = subprocess.check_output(["git", "show", f"{args.reference_revision}:{name}"])
            changed[name] = dict(original_sha256=hashlib.sha256(original).hexdigest(),
                                 current_sha256=hashlib.sha256(data).hexdigest())
    assert set(changed) == allowed
    result = dict(status="PASS", reference_revision=args.reference_revision,
                  checked_files=count, unchanged_files=count-len(changed),
                  changes=changed, all_other_reference_files="byte-identical")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
