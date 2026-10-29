"""Archive an enforced readiness stop; no scientific or package execution."""
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=Path.cwd()
def main():
 read=lambda p:json.loads(Path(p).read_text());a=read(R/'readiness.json');p=read(R/'resource_projection.json');h=read(R/'preservation.json')['historical_sha256']
 assert a['status']=='HOLD' and a['scientific_trajectories']==0 and not a['validation_opened'] and not a['locked_opened'] and p['development_combined_s']>p['development_cap_s']
 assert 'ModuleNotFoundError' in (R/'preflight_import_failure.log').read_text()
 assert not (R/'supervision').exists() and not (R/'development').exists() and not (R/'validation').exists() and not list(R.rglob('*.npz'))
 for path,value in h.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==value,path
 assert read('reports/evidence/m005b_1/decision.json')['engineering']=='PASS'
 decision=dict(readiness='HOLD',audit='COMPLETE',scientific_execution='PARTIAL_NOT_STARTED',scientific_qualification='NOT_EVALUATED',m006='HOLD',starting_revision='901fa5b71784b18bfedabca052420b86cb51460a',review_branch='research/m005b-2-scientific-evaluation',readiness_scope_revision='3735967',blockers=a['blockers'],scientific_trials_acquired=0,validation_trials_acquired=0,locked_networks_opened=False,fresh_pytest_tests_run=0,preflight_launcher_exit=1,prior_m005b1_engineering='PASS_UNCHANGED',historical_files_unchanged=len(h),resource_caps_changed=False,controllers_changed=False,protocol_changed=False,dependencies_installed=False,development_forecast_s=p['development_combined_s'],development_cap_s=p['development_cap_s'],validation_forecast_s=p['validation_s'],validation_cap_s=p['validation_cap_s'])
 (R/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
 source={str(path.relative_to(ROOT)) if path.is_absolute() else str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(R.glob('*.py'))};(R/'source_manifest.json').write_text(json.dumps(source,indent=2)+'\n')
 files=[path for path in R.rglob('*') if path.is_file() and not path.is_symlink() and '__pycache__' not in path.parts and path.name!='manifest.json'];files.extend([Path('reports/M005B_2_ADAPTIVE_CONTROL.md'),Path('docs/research/011_M005B_CONTROL_PROTOCOL.md')]);manifest={str(path.relative_to(ROOT)) if path.is_absolute() else str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
 (R/'manifest.json').write_text(json.dumps(dict(sha256=manifest,excluded='self and Python caches; no scientific data exist'),indent=2)+'\n');print(json.dumps(decision))
if __name__=='__main__':main()
