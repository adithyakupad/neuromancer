Independent timing analysis refinement:the timestamp after a None poll result is not an
exact instant at which the kernel still considered the process alive. A child can exit
between waitpid returning None and the diagnostic clock read. The conservative lower bound
for actual exit is therefore the corresponding poll-BEGIN timestamp. Final verifier outputs
use first observed exit minus that begin as an upper bound on exit-to-observation delay.
Initial v1 analysis outputs are retained; classification,cleanup,source preservation and
all raw timestamps/outcomes are unchanged. Actual kernel exit remains interval-censored.
Sleep envelopes include trace-call overhead, and terminal envelopes include trace persistence;
these are not claims of exact kernel-sleep or isolated fsync timings.
