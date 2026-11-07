"""Retain scoped supervisor fixture evidence on both passing and failing tests."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    report=outcome.get_result()
    setattr(item,'_m008_'+report.when,report)


@pytest.fixture(autouse=True)
def retain_supervisor_evidence(request):
    if Path(str(request.node.path)).name not in ('test_supervisor.py','test_suspend_clock.py','test_supervisor_boundaries.py'):
        yield;return
    root=os.environ.get('NEUROMANCER_TEST_ARTIFACTS')
    if not root:
        yield;return
    temp=request.getfixturevalue('tmp_path')
    yield
    # This finalizer runs even when a lifecycle assertion fails.
    label=hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:16]
    dest=Path(root).resolve()/label;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(temp,dest,symlinks=True)
    reports={phase:getattr(request.node,'_m008_'+phase).outcome for phase in ('setup','call') if hasattr(request.node,'_m008_'+phase)}
    ids=set()
    for f in temp.rglob('pid.json'):
        if not f.is_symlink():ids.add(int(json.loads(f.read_text())['pid']))
    selected={}
    if ids:
        status=subprocess.run(['ps','-p',','.join(map(str,sorted(ids))),'-o','pid=,pgid=,stat='],capture_output=True,text=True,timeout=2)
        selected=dict(returncode=status.returncode,owned_process_rows=status.stdout)
    (dest/'pytest_evidence.json').write_text(json.dumps(dict(nodeid=request.node.nodeid,reports=reports,python=sys.version,platform=platform.platform(),owned_pids=sorted(ids),owned_process_check=selected),indent=2)+'\n')
