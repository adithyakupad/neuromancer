"""Publish verified retrospective findings, not new scientific acceptance gates."""
import csv,json,hashlib,platform,sys
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
from neuromancer.supervisor import Deadline
r=Path(__file__).resolve().parent;Deadline.from_environment().check()
def read(p):return json.loads(Path(p).read_text())
def rows(p):return list(csv.DictReader((r/p).open()))
s=read(r/'summary.json');n=rows('network_diagnosis.csv');tr=rows('trial_diagnosis.csv');w=rows('windows.csv');cal=rows('calibration_diagnostic.csv')
for p in ('lineage_verification.json','original_numerical_verification.json','verification.json','supplement_verification.json'):assert read(r/p)['status']=='PASS'
term=read(r/'supervision/terminal.json');fixed=read(r/'corrected_verifier_supervision/terminal.json');assert term['status']==fixed['status']=='COMPLETED' and term['cleanup_verified'] and fixed['cleanup_verified']
tests=list(ET.parse(r/'tests.xml').getroot().iter('testsuite'));assert sum(int(t.attrib['tests']) for t in tests)==144 and all(int(t.attrib.get('failures',0))+int(t.attrib.get('errors',0))==0 for t in tests)
mean=lambda key:float(np.mean([float(v[key]) for v in n]))
lines=['# M005A.6 — PI recovery failure diagnosis','',
'**Diagnostic execution PASS. Finite-horizon PI undertracking is supported despite demonstrated reference headroom. M005A.5 remains scientific FAIL (stationary PASS, recovery FAIL). M005B remains HOLD.**',
'', '## Revisions, preservation and scope','',
'Starting clean revision `0862a6286260874414636d3de50be7471eac2eff`, branch `research/m005a-5-confirmation`; review branch `research/m005a-6-recovery-diagnosis`. Retrospective diagnostic plan committed at `37ae9171f33fd32186c1085092318f1a02492388`. Final revision is the commit containing this report, recorded exactly in the mission response; recover it with `git log -1 --format=%H -- reports/M005A_6_RECOVERY_DIAGNOSIS.md`. No merge.',
'',
'Inspected original protocol009, amendments010/011, M005A–M005A.5 reports, control/substrate/supervisor sources, selection seal, confirmation lineage, complete observations/actions and verification records. The preservation manifest hashes every starting tracked file, including all negative findings. No historical file, installed source, Kp=10/Ki=5, target, model parameter or acceptance threshold changed. No controller was fitted or retuned. This is retrospective analysis of already inspected development evidence, not a new confirmatory scientific result.',
'',
'All 20 network/noise pairs (networks0–9, repeats41/42) and160 branches were analyzed. The original three versus continuation17 acquisition sessions retain their original identities; they are one ten-network cohort. No new scientific neural experiment was needed or run. Full regression tests include the existing short neural fixtures; that is verification, not a new recovery experiment. Validation and locked-network outcomes were not opened.',
'', '## Metric definitions and why MAE and bias disagree','',
'Output error is d=y−target, so negative bias means undertracking. Controller error is e=target−y. Use original nonoverlapping1s raw recorded E80 rates. Pre=[8,16), immediate=[16,20), frozen late=[20,32); final=[28,32) is descriptive only. Absolute neural time starts51s; efficacy loss occurs67s. Average repeats inside each network before cohort inference. Bootstrap:10,000 paired network draws, PCG64seed20261025, percentile95% intervals. Do not count bins, sectors or repeats as independent networks. Pointwise time-course intervals are not simultaneous confidence bands.',
'',
'The frozen PI reduces late-loss MAE from0.398503Hz for FIXED to0.260456Hz, an improvement0.138047Hz (95%CI0.107292–0.168516), or33.899% mean paired relative improvement. All ten network MAE improvements are positive. Yet full recovery requires at least8/10 joint networks with |bias|<=0.2Hz in addition to MAE<=0.35Hz and other gates. Only five satisfy the bias criterion. Lower absolute error can coexist with a persistent negative mean error during this finite window; the favorable MAE does not override the failed bias gate.',
'', '| PI signed bias window | Mean Hz | Paired network 95% CI Hz |','|---|---:|---|']
for key,label in [('pi_pre_bias_hz','Pre-loss 8–16s'),('pi_immediate_bias_hz','Immediate 16–20s'),('pi_late_bias_hz','Frozen late 20–32s'),('pi_final_bias_hz','Descriptive final 28–32s')]:
 a=s['stats'][key];lines.append(f"| {label} | {a['mean']:.6f} | [{a['ci95'][0]:.6f}, {a['ci95'][1]:.6f}] |")
lines+=['','## All-network diagnosis','',
'Headroom below means MAX observed rate minus the actual calibration-derived target at reduced efficacy, not just MAX−ZERO. MAX is the same fixed admissible C02 allocation in every network; no per-network action oracle is involved. Biases and currents in this table average the two repeats. Minimum headroom is the smaller of the two observed replicate margins.',
'', '| Net | Pre bias | Immediate bias | Frozen late bias | Final bias | Min MAX headroom Hz | q16→q31 pA/channel | ΔI16→32 pA | Classification |','|---:|---:|---:|---:|---:|---:|---|---:|---|']
for v in n:
 lines.append('| '+ ' | '.join([v['network']]+[f"{float(v[k]):.6f}" for k in ('pi_pre_bias_hz','pi_immediate_bias_hz','pi_late_bias_hz','pi_final_bias_hz','min_max_target_margin_hz')]+[f"{float(v['q16_pA']):.3f}→{float(v['q31_pA']):.3f}",f"{float(v['integral_post_delta_pA']):.3f}",v['classification']])+' |')
lines+=['',
'Frozen recovery failures are networks0,2,5,6,8. The other five passed the recovery gates and are labeled PASS_NO_FAILURE rather than being forced into a failure mechanism category. Final-window bias is closer to zero than immediate bias in9/10 networks; network5 is slightly worse (−0.241406→−0.250781Hz). Networks2 and5 still exceed the bias tolerance even in the final4s. These selected-window descriptions cannot retroactively replace the frozen window or prove eventual convergence.',
'', '## Authority: evidence supports A for the failed networks','',
 f"All10 networks bracket the target with ZERO below and MAX above it in BOTH original repeats. Across all20 repeats MAX−target ranges {min(float(v['max_target_margin_hz']) for v in tr):.6f} to {max(float(v['max_target_margin_hz']) for v in tr):.6f}Hz. Network-mean headroom is {s['stats']['mean_max_target_margin_hz']['mean']:.6f}Hz, paired network95%CI {s['stats']['mean_max_target_margin_hz']['ci95']}. Existing evidence is sufficient to reject observed hard-limit exhaustion as the explanation for these five failures; no new neural diagnostic is justified for that question.",
'',
'A = original PI recovery failure despite both-replicate empirical target bracketing; B = demonstrated actuator-constraint infeasibility (not inferred from finite-bank nonresponse); C = failure mechanism unresolved because reference bracketing is absent/mixed. The five passing cases are separately retained. This avoids falsely calling successful networks failures.',
'', '| Class | All ten networks | Descriptive Wilson95% fraction interval |','|---|---|---|']
for key,label in [('A','A: failed PI with observed reference headroom'),('B','B: demonstrated infeasibility'),('C','C: unresolved failed-network reference evidence'),('PASS_NO_FAILURE','Original recovery pass')]:
 v=s['classifications'][key];lines.append(f"| {label} | {v['count']}/10 ({100*v['fraction']:.0f}%) | [{100*v['wilson95'][0]:.1f}%, {100*v['wilson95'][1]:.1f}%] |")
lines+=['',
'Among the five actual failures,5/5 support A under this operational definition (100%; descriptive Wilson95%56.6–100%). These intervals summarize small counts under an iid approximation; the networks are a previously studied development cohort, and the failure subset is selected by the frozen outcome. They do not quantify causal certainty or future biological prevalence. Two repeats provide no reliable per-network confidence interval, so both margins/ranges are reported in trial_diagnosis.csv. Zero B cases is not proof that all targets or future states are feasible.',
'',
'Finite noisy bracketing demonstrates recorded rates above the relevant target under one legal policy. It does not prove continuous interpolation, stable exact target realization, mathematical reachability or success of an implementable controller under every disturbance. MAX overshoots and is not a tracking solution. No lower target or alternate channel oracle was selected.',
'', '## Intervention, integral and saturation accounting','',
 f"PI used zero delivered C02 bound ticks out of{20*1600}LOSS ticks, zero decision clipping events, zero anti-windup blocks and zero integral-clamp attempts, including the terminal update. Overall mean replicate peak dose is {mean('pi_q_peak_pA'):.6f}pA/channel; largest single-replicate peak is {max(float(v['pi_q_peak_pA']) for v in tr):.6f}pA/channel, below120. Channels1/3 are identically zero; channels0/2 match. Total current is2q and remains below240pA. Inactive zero channels must not be counted as active-dose saturation.",
'', '| Decision origin relative time | Mean desired q pA/channel | Mean integral pA | Interpretation |','|---|---:|---:|---|']
for index,note in [(16,'Before any post-loss observation'),(17,'First possible response to completed16–17s bin'),(20,'Start of frozen late window'),(31,'Last delivered1s action')]:lines.append(f"| {index}s | {mean(f'q{index}_pA'):.6f} | {mean(f'I{index}_pA'):.6f} | {note} |")
lines += [f"| 32s | {mean('q32_unused_pA'):.6f} | {mean('I32_pA'):.6f} | Terminal update; never delivered |",'',
 f"Mean feedforward is {mean('qff_pA'):.6f}pA/channel. Mean integral rises by {mean('integral_post_delta_pA'):.6f}pA after loss; all20repeat increments are positive (minimum {min(float(v['integral_post_delta_pA']) for v in tr):.6f}pA). The exact programmed identity ΔI=5Σ(target−observed rate)*1s holds because no clamp/block occurs. During the late window alone, mean ΔI is {mean('late_integral_delta_pA'):.6f}pA. This shows continuing correction rather than a frozen integrator or exhausted actuator. The32s command is deliberately not treated as delivered stimulation.",
'',
'Observation delay is the frozen sample-and-hold design: the action at16s is based on completed pre-loss observations; response to loss first becomes available at17s. The dynamics then raise current over several feedback ticks. This accounting supports incomplete finite-horizon compensation. It does not causally establish that Ki=5, Kp=10 or the1s cadence is uniquely responsible, or that increasing gains would be stable/better. No gains/cadence were varied here.',
'', '## Baselines and calibration','', '| Network | Target Hz | qff pA | STATIC FIXED bias Hz | LOSS FIXED bias Hz | FIXED evoked STATIC→LOSS Hz | LOSS−0.6STATIC response Hz |','|---:|---:|---:|---:|---:|---|---:|']
for v in cal:lines.append(f"| {v['network']} | {float(v['target_hz']):.6f} | {float(v['qff_pA']):.3f} | {float(v['fixed_static_bias_hz']):.6f} | {float(v['fixed_loss_bias_hz']):.6f} | {float(v['fixed_static_evoked_hz']):.6f}→{float(v['fixed_loss_evoked_hz']):.6f} | {float(v['scaling_residual_hz']):.6f} |")
lines+=['',
'All original calibrations passed their frozen validity checks. STATIC FIXED late mean bias is '+f"{mean('STATIC_FIXED_late_bias_hz'):.6f}Hz; LOSS FIXED bias is {mean('LOSS_FIXED_late_bias_hz'):.6f}Hz. STATIC PI late bias is {mean('STATIC_PI10_5_late_bias_hz'):.6f}Hz. ZERO trajectories are exactly identical across gain conditions, and all policies match their own STATIC/LOSS records before loss. Thus the gain intervention, rather than a changed target definition, accounts for the paired divergence under fixed input. Calibration at g=1 is not a verified inverse map at g=.6; no controller was given the true gain.",
'',
 f"The evaluator-only linear heuristic qff/.6 averages {mean('gain_scaled_reference_pA'):.6f}pA/channel, whereas delivered late PI currents remain lower. This is dimensional context under a presumed linear map, not a measured required dose, controller input, fitted model or gain-aware action recommendation. Actual FIXED evoked-response scaling residuals are preserved rather than assuming exactly0.6 response attenuation. Historical calibration uncertainty, network nonlinearity and spontaneous fluctuations remain possible contributors.",
'', '## Target dependence, sectors and excitation','',
'Every target is baseline+1Hz. No different target offsets were randomized, so absolute-target dependence cannot be separated from baseline activity/network identity. Descriptive correlations with late PI bias are reported without p-values or feature selection:',
'', '| Network covariate | Pearson r | Spearman rho |','|---|---:|---:|']
for key,v in s['correlations'].items():lines.append(f"| {key} | {v['pearson']:.6f} | {v['spearman']:.6f} |")
lines+=['',
'Target and baseline correlations are identical by construction. The negative association of integral growth with remaining error is partly built into the PI update itself; it cannot establish harm from integration. Lower calibration slope and less headroom co-vary with larger negative bias, but these are confounded across only ten networks, not causal mechanism tests.',
'',
'All four recorded E-sector trajectories and per-network/window rates are in timecourses.csv/windows.csv. Sector baseline deviations are descriptive, not four imposed targets. The figure below compares matched LOSS−STATIC sector responses; under PI this includes feedback mediation. These observations neither expose unrecorded voltages nor isolate excitatory/inhibitory current pathways. No inhibition ablation/current decomposition is available here, so a specific inhibitory mechanism is unsupported.',
'', '| Net | LOSS late sector0/1/2/3 above own baseline Hz |','|---:|---|']
for index in range(10):
 v=[x for x in w if int(x['network'])==index and x['condition']=='LOSS' and x['controller']=='PI10_5' and x['window']=='late'];lines.append(f"| {index} | "+' / '.join(f"{np.mean([float(x[f'sector{j}_above_baseline_hz']) for x in v]):.6f}" for j in range(4))+' |')
lines+=['',
'Persistent excitation was recomputed for all320designs. PI LOSS last16s has rank11/41 in all20repeats; C02 makes two inputs identical and two zero. FIXED/MAX/ZERO last16s have rank1/41. PI qSD and positive-subspace conditioning are recorded in excitation.json; full design is rank deficient. This establishes dose variation, not independent channel identification or consistent estimation under feedback confounding. No extra excitation was injected.',
'', '## Evidence strength and causal limits','',
'- Matched STATIC/LOSS trajectories with common noise provide simulated causal evidence of the evaluator gain intervention; FIXED has unchanged inputs. PI versus FIXED branches identify the tested policy difference, not superiority of an untested controller.',
'- Exact update reconstruction establishes what PI did, including error accumulation, next-tick timing and absence of saturation/blocking.',
'- Bias/current/slope/sector associations support a finite-horizon recovery interpretation but do not identify a unique dynamical cause. Greater gain, adaptation or MPC superiority has not been tested.',
'- Final-window improvement is not a steady-state experiment. Network5 does not improve in that comparison, and two networks remain beyond0.2Hz even there. No alternate window rescues the original result.',
'', '## Verification, commands and failures','',
'Ran the full existing suite: **144 passed,25existing warnings,58.06s**. Original independent verifier reconstructed20trials/160branches/800primary rows from preserved events, with timing/current/slew/calibration/policy/noise checks. New independent verifier reconstructed640diagnostic windows,5120one-second rows,2560matched contrasts,1280scalar PI updates, network aggregation/correlations/bootstrap, and320excitation references without importing the producer. Supplemental verification independently checked ten calibration contrasts and256pointwise network intervals. Source/Git/selection and all starting evidence hashes passed.',
'',
'One supplemental CSV verifier initially failed because it passed CSV strings to NumPy numeric comparison. The supervisor correctly recorded WORKER_FAILURE and reaped the child. Explicit float conversion corrected the verifier; only this read-only verifier was rerun under the SAME original deadline. No data, model, thresholds or numerical producer changed. Failed source, logs, terminal record and correction provenance are retained. This was not a neural/scientific retry or a resource failure.',
'', '```sh',
'/tmp/neuromancer-m004-venv/bin/python reports/evidence/m005a_6/run_commands.py reports/evidence/m005a_6/stage_config.json',
'# Exact original and supplemental child commands are in stage_config.json and supplement_config.json.',
'# Corrected verifier and report publication inherit supervision/terminal.json deadline and clock domain.',
'```', '',
'Environment: Python3.12.15, Brian2 2.10.1, NumPy2.5.4, macOS arm64; requested VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/neuromancer-m005a-mpl. Actual BLAS threading is not certified. Main1200s supervisor stage completed in '+f"{(term['finished_ns']-term['started_ns'])/1e9:.6f}s with cleanup verified. Corrected verification inherited the exact same absolute deadline/boot domain. Independent reconstruction here is within-session verification, not external replication. No new scientific acquisition or locked-network test ran.",
'', '## Stronger-control decision and next falsifiable experiment','',
'Further recovery-dynamics research is justified by demonstrated reference headroom and incomplete correction, but stronger/adaptive control is **not scientifically qualified or shown necessary**. An unchanged PI might recover with more time; alternatives might amplify noise or overshoot. The diagnosis therefore supports hypothesis A for the five failures at the finite tested horizon, with explicit empirical-reachability limits. There is no observed support for B as the dominant explanation and no failed-network C case under the prespecified bracketing rule. Unique causal attribution remains uncertain.',
'',
'**M005B HOLD.** Do not implement MPC or retune PI on these outcomes. Next proposal, requiring a separate preregistration/authorization: extend the unchanged fixed-PI STATIC/LOSS experiment to64s on all ten development networks with fresh prespecified noise, retain/report the original20–32s window unchanged, and test whether signed bias moves toward zero in48–64s without saturation. Keep target, Kp/Ki, calibration and constraints identical; retain matched MAX/ZERO/FIXED references. This distinguishes slow convergence from longer-lived offset and cannot reclassify M005A.5. An optional separate integral-freeze or cadence ablation would be needed to causally isolate feedback mechanisms; neither was run here.',
'',
'Primary limitations: only ten previously studied networks/two repeats; final-window and correlation analyses are retrospective; MAX bracketing is noisy finite-policy evidence, not a mathematical reachable set; no long-horizon convergence/stability, gain/cadence ablation, hidden-current mechanism or biological experiment was measured.',
'', '## Deliverables','',
'[Bias dynamics](evidence/m005a_6/bias_dynamics.png), [current/integral histories](evidence/m005a_6/current_integral.png), [authority and sectors](evidence/m005a_6/authority_sectors.png). Complete per-repeat/per-network metrics, all32s histories, calibrated targets, original source references, network uncertainty and independent verification are under `reports/evidence/m005a_6/`. Original raw neural observations/actions remain at their immutable M005A.5 paths; the input manifest links them by hash rather than duplicating trials.']
designs=read(r/'excitation.json')
pe=[x for x in designs if x['controller']=='PI10_5' and x['condition']=='LOSS' and x['window']=='last16']
lines+=['', 'PI LOSS last16s delivered-dose variability and identifiable-subspace conditioning by network (means of two repeats):', '', '| Net | q SD pA | Positive-subspace condition | Full rank |', '|---:|---:|---:|---|']
for net in range(10):
 vals=[x for x in pe if x['network']==net];lines.append(f"| {net} | {np.mean([x['q_sd_pA'] for x in vals]):.6f} | {np.mean([x['positive_condition'] for x in vals]):.6f} | 11/41 |")
import re
text='\n'.join(lines)+'\n'
text=re.sub(r'(\d)(?=(?:Hz|pA|s|ms|us|LOSS|repeat|paired|joint|existing|scalar|pointwise|primary|diagnostic|trials|branches|matched|networks|samples|designs|ticks)\b)',r'\1 ',text)
text=text.replace('PCG64seed','PCG64 seed ').replace('All10','All 10').replace('all20','all 20').replace('all32','all 32').replace('all320','all 320').replace('networks0','networks 0').replace('repeats41','repeats 41').replace('network5','network 5').replace('Networks2','Networks 2').replace('network95%CI','network 95% CI').replace('Wilson95%','Wilson 95%')
Path('reports/M005A_6_RECOVERY_DIAGNOSIS.md').write_text(text)
(r/'decision.json').write_text(json.dumps(dict(execution='PASS',diagnosis='Finite-horizon undertracking despite empirical reference headroom; unique causal mechanism unproven',classifications=s['classifications'],new_scientific_trials=0,original_m005a5_scientific='FAIL',m005b='HOLD',controller_changes=0,tests_passed=144),indent=2)+'\n')
(r/'environment.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in r.glob('*.py')}),indent=2)+'\n');Deadline.from_environment().check()
