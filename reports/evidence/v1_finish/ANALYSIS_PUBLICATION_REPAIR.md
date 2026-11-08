# Analysis publication repair — no scientific change

Primary acquisition completed20/20trials and260/260branches. Raw reconstruction PASS:832000bins,384000model-state hashes,4800000candidate scores,zero violations/fallbacks/invalid models.

The first independent-statistics worker completed all raw-calibration, metric, bootstrap and scientific-gate assertions, then failed at atomic_json because its CLI output string had not been converted to Path. The complete original worker log and PARTIAL post_acquisition_failure.json remain unchanged. Main analysis outputs are complete. This is a publication defect, not a new scientific result or a reason to rerun neural trials.

Convert only the output argument to Path in verify_metrics.py and the same latent publication pattern in prediction_summary.py. No arithmetic, target, model, endpoint, seed, window, threshold or decision changes. Extend the existing analytical test to pass the CLI string type in both PASS and FAIL fixtures. Rerun these fixtures and the independent verifier under the SAME original analysis deadline from analysis_launch.json. Preserve all previous outputs/failure markers.

After independent publication succeeds, freeze the already specified primary decision and acquire only the originally required secondary faults, with the SAME original development deadline from primary_launch.json. No primary reacquisition or replacement. The failed original orchestration remains PARTIAL; a separate recovery record documents completion. Validation remains closed because the original primary superiority gate versus PI fails. This repair neither authorizes validation nor changes its rule.
