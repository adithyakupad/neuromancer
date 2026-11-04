Preliminary hosted ba4d3be9 legacy41792872132 and matrix41792872129 failed fixture setup:
--basetemp=runs/pytest-tmp requires its parent runs/ to exist. A fresh checkout lacks runs/;
pytest creates only the final basetemp directory, while JUnit creates runs/ only at session end.
Local report paths already had parents, so local tests did not expose this CI-only setup defect.
Legacy:151passed,65setup errors,25warnings,45.13s. No worker timing success is inferred for
cases that failed setup. Original logs preserved; matrix outcomes retained separately.

Smallest repair:add mkdir -p runs before pytest in both workflows. No test,deadline,solver,
fixture logic or expected outcome changed. No blind rerun:the source/configuration changes
are committed and requalified. Artifact upload remains if:always().
