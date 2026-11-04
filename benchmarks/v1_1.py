"""Bounded V1.1 engineering measurements, never scientific acquisition."""
import argparse,cProfile,hashlib,importlib.metadata,json,os,pickle,platform,pstats,resource,subprocess,sys,time,tracemalloc
from pathlib import Path
import numpy as np
from neuromancer.supervisor import Deadline,supervise,atomic_json

def measured(f):
    w=time.perf_counter_ns();c=time.process_time_ns();v=f()
    return v,dict(wall_s=(time.perf_counter_ns()-w)/1e9,cpu_s=(time.process_time_ns()-c)/1e9)
def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def fixture():
    from neuromancer.predictive import initialize_raw
    rng=np.random.default_rng(20261106);q=rng.uniform(0,120,2550)
    for k in range(1,len(q)):q[k]=np.clip(q[k],q[k-1]-30,q[k-1]+30)
    u=np.zeros((2550,4));u[:,::2]=q[:,None];y=np.full((2550,4),8.)
    for lag in range(10):y[9:]+=.0005*(lag+1)*q[9-lag:2550-lag,None]
    return (*initialize_raw(y,u),u,y)
def child(out,kind):
    d=Deadline.from_environment();d.check();out.mkdir(parents=True,exist_ok=False);rows=[];signatures=[]
    if kind=='micro':
        from neuromancer.predictive_planner import plan,bank
        from neuromancer.predictive import FIRModel
        from neuromancer._brian import innovations
        from neuromancer.substrate import Config
        (rec,z,v,p,u,y),fit=measured(fixture);times=[];bank_times=[];update=[];pred=[];dig=hashlib.sha256();model=FIRModel(rec,p,'RLS');prof=cProfile.Profile()
        for i in range(100):
            d.check();h=np.zeros((9,4));h[:,::2]=float((i*17)%121)
            result,t=measured(lambda:plan(rec,rec['coef'],h,9.+i%3*.1,51_000_000));times.append(t)
            _,t=measured(lambda:bank(h[-1,0]));bank_times.append(t)
            x=u[2400+i-9:2401+i][::-1].ravel();yy,t=measured(lambda:model.predict(x));pred.append(t)
            _,t=measured(lambda:model.update(x,y[2400+i]));update.append(t)
            for name in ('predictions','cost','bank','first'):dig.update(np.ascontiguousarray(result[name]).tobytes())
            dig.update(str(result['chosen']).encode());dig.update(model.theta.tobytes());dig.update(model.p.tobytes())
        prof.enable();plan(rec,rec['coef'],h,9.,51_000_000);prof.disable();prof.dump_stats(out/'micro.prof');pstats.Stats(prof,stream=(out/'micro_profile.txt').open('w')).sort_stats('cumtime').print_stats(35)
        noise=[]
        for k in range(3):
            d.check();tracemalloc.start();(a,h),t=measured(lambda:innovations(Config(),k));_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();noise.append(dict(**t,peak_traced_bytes=peak,effective=sha(a),fine=h))
        arr=np.arange(200000,dtype=np.int64);storage={}
        for compressed in (False,True):
            path=out/('compressed.npz' if compressed else 'plain.npz');_,w=measured(lambda:(np.savez_compressed if compressed else np.savez)(path,events=arr));loaded,r=measured(lambda:np.load(path)['events']);assert np.array_equal(arr,loaded);storage[str(compressed)]=dict(write=w,read=r,bytes=path.stat().st_size)
        atomic_json(out/'result.json',dict(fit=fit,planner=times,bank=bank_times,rls=update,fir=pred,signature=dig.hexdigest(),noise=noise,storage=storage))
    else:
        from neuromancer._brian import BrianEngine
        from neuromancer.substrate import Config,Command,Trial
        from neuromancer.diagnostic import run_hold
        if kind=='ipc':
            def go():
                with Trial(Config()) as trial:
                    for k in range(50):
                        t=k*20000;result=trial.advance(Command('trial',str(k),t,(0.,)*4),t+20000)
                return result.observation.counts
            counts,t=measured(go);rows.append(dict(kind=kind,**t,last_counts=counts))
        else:
            engine,init=measured(lambda:BrianEngine(Config(retain_spikes=True)));prof=cProfile.Profile()
            for rep in range(3):
                for chunk in (False,True):
                    d.check();engine.reset();result,t=measured(lambda:run_hold(engine,1,60,chunked=chunk));rs,_=result
                    a=np.array([r.observation.counts for r in rs]);events=np.c_[np.asarray(engine.monitor.i),np.rint(np.asarray(engine.monitor.t)*1e6).astype(np.int64)];signature=sha(events)+sha(a);signatures.append(signature)
                    rows.append(dict(rep=rep,chunked=chunk,**t,simulated_s=1,neural_s=sum(r.neural_wall_ns for r in rs)/1e9,observation_s=sum(r.observation_wall_ns for r in rs)/1e9,signature=signature,events=len(events)))
            engine.reset();prof.enable();run_hold(engine,1,60,chunked=True);prof.disable();engine.reset();original=engine.net.run
            def profile_run(*args,**kwargs):return original(*args,profile=True,**kwargs)
            engine.net.run=profile_run;run_hold(engine,1,60);atomic_json(out/'brian_codeobjects.json',[(name,float(value)) for name,value in engine.net.profiling_info]);engine.net.run=original
            _,save=measured(lambda:engine.save('bench'));_,restore=measured(lambda:engine.restore('bench'));engine.close();assert len(set(signatures))==1
            prof.dump_stats(out/'neural.prof');pstats.Stats(prof,stream=(out/'neural_profile.txt').open('w')).sort_stats('cumtime').print_stats(60)
            atomic_json(out/'checkpoint.json',dict(initialization=init,save=save,restore=restore))
        atomic_json(out/'result.json',dict(rows=rows))
    d.check();rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert rss<=4294967296
    atomic_json(out/'process.json',dict(peak_rss_bytes=rss,cpu_s=time.process_time(),remaining_s=d.remaining()))
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--child');a=p.parse_args()
    if a.child:return child(a.output,a.child)
    a.output.mkdir(parents=True,exist_ok=False);d=Deadline.after(900);os.environ.update(NEUROMANCER_DEADLINE_NS=str(d.end_ns),NEUROMANCER_DEADLINE_CLOCK=d.clock_id,OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR='/tmp/neuromancer-perf-mpl')
    atomic_json(a.output/'environment.json',dict(python=sys.version,platform=platform.platform(),cpu=platform.processor(),logical_cpu=os.cpu_count(),packages={x:importlib.metadata.version(x) for x in ('numpy','brian2','scipy','pytest')},thread_requests='1; actual OS/BLAS threads not established',source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),manifest=json.loads(Path('benchmarks/v1_1_manifest.json').read_text())))
    for kind in ('micro','neural','ipc'):
        r=supervise([[sys.executable,__file__,'--child',kind,'--output',str(a.output/kind)]],a.output/(kind+'_supervision'),d,workers=1);assert r['status']=='COMPLETED',r
    # Identical independent process workload, fixed total two jobs; startup included.
    for n in (1,2):
        begin=time.perf_counter();commands=[[sys.executable,__file__,'--child','ipc','--output',str(a.output/f'workers{n}_{i}')] for i in range(2)]
        r=supervise(commands,a.output/f'workers{n}_supervision',d,workers=n);assert r['status']=='COMPLETED';atomic_json(a.output/f'workers{n}.json',dict(wall_s=time.perf_counter()-begin,total_simulated_s=2))
    # Separate cold subprocess startup; OS filesystem cache is not flushed.
    startup=[]
    for i in range(3):
        _,t=measured(lambda:subprocess.run([sys.executable,'-c','import neuromancer, numpy, brian2, scipy'],check=True,timeout=min(30,d.remaining())));startup.append(t)
    atomic_json(a.output/'startup.json',startup);atomic_json(a.output/'complete.json',dict(status='PASS',remaining_s=d.remaining()))
if __name__=='__main__':main()
