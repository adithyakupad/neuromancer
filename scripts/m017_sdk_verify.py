"""Use the original SDK receipt checks with the V2 preservation manifest."""
import json
from pathlib import Path
import sys

from m016_verify import verify
from m017_reproduce import verify_history

if __name__ == "__main__":
    root = Path(sys.argv[1])
    result = verify(root, verify_base=verify_history)
    root.with_name(root.name + "_verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
