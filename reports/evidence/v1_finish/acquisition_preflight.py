"""Frozen scientific-runner preflight; tests plus nonreserved2s integration."""
import json,sys
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise
r=Path(__file__).resolve().parent;d=Deadline.after(1200)
commands=[[sys.executable,'-m','pytest','-q','--basetemp='+str(r/'acquisition_preflight_fixtures'),'--junitxml='+str(r/'acquisition_preflight_tests.xml')],[sys.executable,'-m','neuromancer.m005b_study','inner','engineering',str(r/'runner_smoke')]]
x=supervise(commands,r/'acquisition_preflight_supervision',d,workers=1);print(x['status']);assert x['status']=='COMPLETED'
