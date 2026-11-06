# Operation Recover prospective engineering plan

Base M019 archive 321e702fea90688bb232e324c2ec5f8b9a474aa2.
Reliability and recording share one diagnostic branch. Style runs
from a separate branch and scientific designs start from the release
source. The release ref and historical evidence remain immutable.

M020 runs four standalone sessions per arm and host, unmodified
then traced SDK 1.0.0, with a synthetic timestamp-coded source and
HDF5 recording. The traced arm uses an ephemeral byte-checked wheel
copy and instruments producer polling entry, request load, command
return, stimulus handling, source callback and write completion.
Each session has 16 windows of 500 frames. Trace overhead may
perturb occurrence. If a frame timeout occurs, the last producer
event bounds the observed failure, without proving OS dispatch.

M021 runs three sessions per lifecycle mode and host, in before,
after, bounded order. Before stops while the final iterator yield is
active. After exhausts the iterator and waits a fixed 30 ms before
manual stop. Bounded uses public stop_after_frames=8000 and waits for
automatic closure. Save the original recording, consumed endpoints,
explicit final-frame metadata and sample/event replays. Before and
bounded must produce exactly 8000 frames. After reports the actual
extent without trimming. No-stimulation event tests use spikes at
each bin's first and last frame. This is a recording-contract
diagnostic and has no controller or biological outcome.

The hosted diagnostic runs once per platform, Linux and macOS Intel.
The original 100 ms internal wait and 120 s watchdog per arm remain.
The job limit is 16 minutes. Stop a condition at its first failure.
Continue only if cleanup verifies. No repeat after outcome inspection.
One local preflight per each of the five fixed arms is permitted,
with the same deadlines, before hosted dispatch. Keep all failures.
A passing diagnostic is not full SDK release qualification.

M022 uses the already published counterbalanced 12-pair design,
with M017 frozen source and current style revision. Operation
Recover authorizes measuring this isolated style branch independently
of SDK publication. The exact gates and 30 min, 2 GiB resource caps
stand. No other local benchmark, build or regression runs concurrently.
