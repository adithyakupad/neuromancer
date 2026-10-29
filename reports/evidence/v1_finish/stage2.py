import sys,json
from pathlib import Path
from neuromancer.supervisor import Deadline,supervise
r=Path(__file__).resolve().parent;d=Deadline.after(1200)
x=supervise([[sys.executable,str(r/'profile.py')]],r/'stage2_supervision',d,workers=1)
print(x['status']);assert x['status']=='COMPLETED'
