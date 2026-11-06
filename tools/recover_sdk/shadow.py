"""Build a disposable CL SDK 1.0.0 diagnostic copy. Never edit site-packages."""
import hashlib
from importlib import metadata
import json
from pathlib import Path
import shutil
import sys

EXPECTED = '3626ca8a3444190d580b5c248a14f9babfed467262d3d664b57abd4e401fe87a'
HELPER = '''
import os as _recover_os
_recover_fd = None

def _recover_trace(event, cursor, request):
    global _recover_fd
    if _recover_fd is None:
        _recover_fd = _recover_os.open(_recover_os.environ["RECOVER_PRODUCER_TRACE"],
            _recover_os.O_WRONLY | _recover_os.O_CREAT | _recover_os.O_APPEND, 0o600)
    row = f"{time.monotonic_ns()},{_recover_os.getpid()},{event},{cursor},{request}\\n"
    _recover_os.write(_recover_fd, row.encode("ascii"))

'''


def build(destination):
    sdk = metadata.distribution('cl-sdk')
    if sdk.version != '1.0.0':
        raise ValueError('Only the audited SDK 1.0.0 wheel is supported')
    source = Path(sdk.locate_file('cl'))
    relative = Path('_sim/_data_producer.py')
    original = (source / relative).read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED:
        raise ValueError('Producer source differs from the audited wheel')
    shutil.copytree(source, destination / 'cl', ignore=shutil.ignore_patterns('__pycache__'))
    text = original.decode()
    replacements = [
        ('_logger = logging.getLogger', HELPER + '_logger = logging.getLogger'),
        ('                spin_count   = 0',
         '                _recover_trace("wait_check", self._current_timestamp, requested_ts)\n'
         '                spin_count   = 0'),
        ('                if not self._running:\n                    break\n\n                self._process_commands()',
         '                if not self._running:\n                    break\n\n'
         '                _recover_trace("request_loaded", self._current_timestamp, requested_ts)\n'
         '                self._process_commands()\n'
         '                _recover_trace("command_done", self._current_timestamp, requested_ts)'),
        ('            self._deliver_stims_to_source(to_ts)\n            batch  =',
         '            _recover_trace("stim_begin", from_ts, to_ts)\n'
         '            self._deliver_stims_to_source(to_ts)\n'
         '            _recover_trace("callback_enter", from_ts, to_ts)\n            batch  ='),
        ('            frames = self._coerce_frames',
         '            _recover_trace("callback_return", from_ts, to_ts)\n'
         '            frames = self._coerce_frames'),
        ('            self._buffer.write_frames_validated(frames, from_ts)',
         '            self._buffer.write_frames_validated(frames, from_ts)\n'
         '            _recover_trace("written", from_ts, to_ts)'),
    ]
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError('Producer instrumentation anchor is ambiguous')
        text = text.replace(old, new, 1)
    compile(text, str(relative), 'exec')
    patched = text.encode()
    (destination / 'cl' / relative).write_bytes(patched)
    (destination / 'identity.json').write_text(json.dumps(dict(
        sdk=sdk.version, variant='M020-diagnostic-only',
        original_sha256=EXPECTED, traced_sha256=hashlib.sha256(patched).hexdigest(),
    ), indent=2) + '\n')


if __name__ == '__main__':
    build(Path(sys.argv[1]))
