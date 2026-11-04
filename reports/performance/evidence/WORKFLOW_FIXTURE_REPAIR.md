Two supplementary benchmark setup failures are retained. First, the harness failed to
unpack project()'s (current,status) return and passed that two-item tuple as a command;
the released four-channel validator correctly rejected it before neural integration.
The first attempted harness repair converted scalars but still had the unpacking error,
so failed in harness code before delivery. Both process-group cleanups verified.
The corrected harness unpacks (current,status) and maps the four values to built-in floats,
matching production adapters. Both reference/optimized comparisons use this same corrected
fixture. No production defect, scientific result, successful timing or optimization benefit
is inferred from either failed attempt. Logs/output directories remain preserved.
