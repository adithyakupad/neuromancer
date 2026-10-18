"""Training-network-0 mechanism diagnostic after frozen authority gate failure.
Run from the repository: python reports/evidence/m002/mechanism_probe.py OUTPUT_DIR
No model parameters or public observations are changed.
"""
import json
from pathlib import Path
import sys
import brian2 as b
from brian2.codegen.runtime.numpy_rt import NumpyCodeObject
import numpy as np
from neuromancer import Config
from neuromancer._brian import BrianEngine
from neuromancer.diagnostic import run_hold, rates, provenance


def main():
    output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=False)
    engine=BrianEngine(Config())
    run_hold(engine,5,0);run_hold(engine,10,0)
    trace=b.StateMonitor(engine.group,['I_E','I_I'],record=True,dt=.02*b.second,
                         when='end',codeobj_class=NumpyCodeObject)
    engine.net.add(trace)
    engine.save('baseline')
    stimulus=engine.parameters['stimulation'].ravel()
    recorded_e=engine.parameters['recording'].reshape(4,5,5)[:,:4,:].ravel()
    groups={'stimulated_E':stimulus,'recorded_unstimulated_E':recorded_e,
            'hidden_unstimulated_E':np.setdiff1d(np.arange(800),np.r_[stimulus,recorded_e]),
            'all_I':np.arange(800,1000)}
    result={}
    for label,amplitude,gain in [('sham',0,1),('stim_g1',60,1),('stim_g06',60,.6)]:
        engine.restore('baseline');engine.group.gain=gain
        before=np.asarray(engine.monitor.count).copy()
        observations,_=run_hold(engine,5,amplitude)
        firing=(np.asarray(engine.monitor.count)-before)/5
        result[label]={'recorded_E_hz':float(rates(observations).mean()),'groups':{}}
        for name,members in groups.items():
            result[label]['groups'][name]=dict(neurons=len(members),rate_hz=float(firing[members].mean()),
                mean_exc_current_pA=float(np.mean(trace.I_E[members]/b.pA)),
                mean_inh_current_pA=float(np.mean(trace.I_I[members]/b.pA)))
        np.savez_compressed(output/f'{label}.npz',time_us=np.rint(trace.t/b.us).astype(np.int64),
                            exc_current_pA=trace.I_E/b.pA,inh_current_pA=trace.I_I/b.pA,
                            per_neuron_rate_hz=firing)
    # Verify that adding an evaluator monitor did not change the frozen result.
    assert abs(result['sham']['recorded_E_hz']-12.75)<1e-12
    assert abs(result['stim_g1']['recorded_E_hz']-15.2025)<1e-12
    assert abs(result['stim_g06']['recorded_E_hz']-14.245)<1e-12
    result['provenance']=provenance()
    result['interpretation']='Descriptive group rates/currents; no causal ablation of inhibition was performed.'
    (output/'mechanism.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value['groups'] for key,value in result.items() if key in ['sham','stim_g1','stim_g06']},indent=2))


if __name__=='__main__':main()
