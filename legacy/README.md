# Baseline experiment source

This directory contains finite-field utilities and four experiment modules.
No precomputed data or plots are distributed.

Use `python run_experiments.py` from the repository root to generate baseline
data and execute the supplements in the correct order. Alternatively,
`python legacy/run_all.py` runs only the baseline suite.

The baseline runner executes unittest discovery, sparse-mask prefix ranks,
overlap and extra-exposure checks, resource sweeps and plots, and uniform-degree
separable-mask ranks. It checks freshly generated outputs and writes a manifest
to `validation/run_manifest.json`.

`run_all.py --quick` reduces sweep sizes and overwrites baseline outputs; it is
not input for the full-size supplement's cost comparisons. Use the root full
runner before executing those comparisons.

These are algebraic checks and resource models, not deployed protocol security
or measured network performance.
