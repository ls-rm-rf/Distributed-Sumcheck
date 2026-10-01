# Experiment modules

This directory contains finite-field utilities and four experiment modules.
Use `python run_experiments.py` from the bundle root for the full workflow.
The root runner first calls `legacy/run_all.py`, then runs the complete-refresh,
joint-prefix, cost-comparison, and epoch-plot scripts in their experiment modules.

`python legacy/run_all.py` runs the baseline suite only: unittest discovery,
sparse-mask prefix ranks, overlap and extra-exposure checks, resource sweeps
and plots, and uniform-degree separable-mask ranks. It verifies generated
baseline files and all experiment source, then writes
`legacy/validation/run_manifest.json`. Later stages write their outputs to each
module's `validation/` and `figures/` directories, outside the baseline manifest.

The complete-refresh and joint-snapshot checks live in `exp2_barrier/`.
Complete-refresh cost comparisons live in `exp3_communication/`.
The root [README](../README.md) lists individual scripts and output paths.

`run_all.py --quick` reduces sweep sizes and overwrites baseline outputs.
These reduced data cannot satisfy the full cost comparison. Run the root
full workflow to regenerate the required parameter coverage.

These are algebraic checks and resource models, not a deployed protocol
or measurements of network performance.
