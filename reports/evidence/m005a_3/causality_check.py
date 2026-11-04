"""Public-only controller replay and synthetic mutation/fault fixtures.

No future rate, counterfactual, engine, true gain or trial.json is loaded into
Policy. These modified observations are software fixtures, not neural results.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from neuromancer.control import ControlCalibration,Policy,project
from neuromancer.observation import Observation


def replay(counts,times,coverage,valid,c,name):
    policy=Policy(c,name);prior=np.zeros(4);u=[];states=[];safe=[]
    for k in range(1600):
        if k%50==0:states.append(policy.record())
        action,_=project(policy.desired(),prior);u.append(action);prior=action
        o=Observation('public-controller-fixture',*map(int,times[k]),tuple(map(int,counts[k])),(0.,)*20,
                      tuple(map(int,coverage[k])),tuple(map(bool,valid[k])),(),(),(0.,)*4,(0.,)*4,True)
        policy.accept(o,int(times[k,2]));safe.append(policy.safe)
    return np.array(u),np.array(states),np.array(safe)


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);p.add_argument('selection',type=Path);a=p.parse_args()
    name=json.loads(a.selection.read_text())['controller'];folder=a.raw/'n0_r41';c=ControlCalibration(**json.loads((folder/'calibration.json').read_text()))
    path=folder/f'LOSS_{name}.npz';d=dict(np.load(path));args=(d['time_us'],d['coverage_us'],d['valid'],c,name)
    u,states,safe=replay(d['counts'],*args)
    np.testing.assert_array_equal(u,d['delivered']);np.testing.assert_array_equal(states,d['decisions']);assert not safe.any()
    changed=d['counts'].copy();changed[500:]+=7
    uf,sf,_=replay(changed,*args)
    np.testing.assert_array_equal(u[:500],uf[:500]);np.testing.assert_array_equal(states[:11],sf[:11])
    past=d['counts'].copy();past[:50]+=1
    up,_,_=replay(past,*args);np.testing.assert_array_equal(up[:50],u[:50]);assert not np.array_equal(up[50:],u[50:])
    counts=d['counts'].copy();counts[500]=-1;mask=d['valid'].copy();mask[500]=False;coverage=d['coverage_us'].copy();coverage[500]=0
    ud,_,sd=replay(counts,d['time_us'],coverage,mask,c,name)
    assert sd[500] and not sd[504]
    assert np.all(ud[501]<=ud[500]) and np.all(abs(ud[501]-ud[500])<=30)
    a.output.write_text(json.dumps(dict(status='PASS',kind='synthetic softwarefixtures from public records',
        controller=name,neural_trajectories_acquired=0,exact_replayed_commands=1600,exact_decision_states=32,
        future_mutation_at_us=61000000,unchanged_past_commands=500,unchanged_past_decisions=11,
        past_observation_mutation_changes_future_actions=True,dropout_next_tick_safe=True,four_fresh_bins_rearm=True,
        source_public_sha256=hashlib.sha256(path.read_bytes()).hexdigest()),indent=2)+'\n')


if __name__=='__main__':main()
