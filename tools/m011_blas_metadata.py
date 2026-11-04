"""Current build/thread metadata, not a timing benchmark or historical proof."""
import importlib.util
import json
import os
import platform
from pathlib import Path
import sys

import numpy as np

output = Path(sys.argv[1])
# Tiny backend initialization only; no elapsed-time or throughput score is taken.
np.ones((8, 8)) @ np.ones((8, 8))
record = dict(python=sys.version, platform=platform.platform(), numpy=np.__version__,
    requests={name:os.environ.get(name) for name in
              ("VECLIB_MAXIMUM_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
    configuration=np.__config__.show(mode="dicts"),
    threadpoolctl_available=importlib.util.find_spec("threadpoolctl") is not None,
    past_M010_thread_counts="NOT_VERIFIED", active_operation_threads="NOT_MEASURED")
if record["threadpoolctl_available"]:
    from threadpoolctl import threadpool_info
    record["current_library_configuration"] = threadpool_info()
output.write_text(json.dumps(record, indent=2, default=str) + "\n")
print(json.dumps({key:record[key] for key in ("requests", "threadpoolctl_available")}))
