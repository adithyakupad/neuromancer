# V2 quickstart

Use Python 3.12 on POSIX. From the repository root, install the pinned
core stack in a new environment.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-v1.txt
.venv/bin/python -m pip wheel --no-build-isolation --no-deps . -w dist
.venv/bin/python -m pip install --no-deps dist/neuromancer-2.0.0rc1-py3-none-any.whl
.venv/bin/python -m pip check
.venv/bin/neuromancer-diagnostic --mode smoke --output /tmp/v2-installed-smoke
```

Use fresh output directories. These commands run from the source checkout
because the research probes use versioned fixtures and historical archives.

## A. Brian2 engineering feedback

```sh
PYTHONPATH="$PWD/src" .venv/bin/python scripts/m014_supervise.py /tmp/v2-a-supervision 240 .venv/bin/python scripts/m017_probe.py /tmp/v2-a --neural
```

The probe uses synthetic calibration for a short network-0 PI exercise.
It projects current, advances the public trial, predicts with FIR,
updates RLS from the receipt-aligned observation, and repeats after
reset. The trace is an integration check. The controller-efficacy
comparison is the frozen V1 study.

## B. Neural computation evidence

```sh
PYTHONPATH="$PWD/src" .venv/bin/python scripts/m014_supervise.py /tmp/v2-b-supervision 240 .venv/bin/python scripts/m017_reproduce.py /tmp/v2-b
```

The verifier copies M013/M014 archives to scratch, checks the observed
labels, counts, coefficients and controls, and reproduces the pilot
summaries. Raw historic data are versioned in the checkout.

## C. Experimental SDK simulator feedback

**Experimental only, not reliability-qualified.** CL SDK 1.0.0 accelerated sessions can intermittently stall on macOS Intel after the consumer publishes a frame request and before the producer enters the source callback. The original internal 100 ms wait is preserved; the recording-extent repair does not fix this scheduling issue. This synthetic simulator example has no physical MEA/CL1 or living-neuron validation. Use the separate pinned SDK environment, retain the hardware interlock, and do not use this integration for reliability-sensitive or hard-real-time operation. See [Issue #7](https://github.com/adithyakupad/neuromancer/issues/7) and [the core scope](V2_CORE_RELEASE_SCOPE_REVIEW.md).

```sh
python3.12 -m venv /tmp/v2-sdk-env
/tmp/v2-sdk-env/bin/python -m pip install cl-sdk==1.0.0
export PYTHONPATH="$PWD/src"
/tmp/v2-sdk-env/bin/python scripts/m016_watch.py /tmp/v2-c 120 /tmp/v2-sdk-env/bin/python scripts/m016_run.py /tmp/v2-c matrix
/tmp/v2-sdk-env/bin/python scripts/m017_sdk_verify.py /tmp/v2-c
```

The committed response is synthetic. The recording verifier reconstructs
counts and checks each accepted pulse against its source callback and
HDF5 event. The hardware interlock runs before any SDK session opens.
