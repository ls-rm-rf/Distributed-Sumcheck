# Source provenance

The finite-field utilities and baseline experiments in `legacy/` come from
the author's existing V3 refreshable-sumcheck project.

The complete-refresh sampler, lifted-rank, cross-epoch, and joint-snapshot
checks are integrated into `legacy/exp2_barrier/`. The completed-refresh
resource comparison is integrated into `legacy/exp3_communication/`.
The recovery-epoch plotting script also lives in `legacy/exp2_barrier/`.
The reorganization preserves the numerical checks and parameter sets.

The full workflow generates baseline data and a hash manifest before checking
complete refresh. The manifest records baseline outputs and experiment source;
later module outputs are written separately to `validation/` and `figures/`
and have their own check summaries.

Precomputed data, plots, and local environments are not required inputs.
The source release contains code, dependency files, and documentation.
`run_experiments.py` regenerates the outputs and records the status of every stage.
