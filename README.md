# Paper experiments

中文说明：[README.zh-CN.md](README.zh-CN.md).

## Run from scratch

Use Python 3.10 or later. From this directory:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_experiments.py
```

`requirements.lock.txt` records the dependency versions of the original Python
3.14.4 environment. Use it instead of `requirements.txt` to install those versions.
WSL and LaTeX are not required. After installing dependencies, execution needs
neither network access nor files outside this bundle.

The runner performs the baseline sweeps, complete-refresh checks, joint
prefix/snapshot checks, complete-refresh cost comparisons, and epoch-curve
plotting in that order. It regenerates the required data before reading it.
Failures return a nonzero exit status. Do not use `-O` or `PYTHONOPTIMIZE`:
the mathematical checks use assertions.

## Code layout

| Path | Purpose |
|---|---|
| `legacy/crypto_core/` | Finite-field, polynomial, rank, and Shamir utilities |
| `legacy/exp1_rank_saturation/` | Sparse-mask prefix ranks |
| `legacy/exp2_barrier/` | Overlap, cross-epoch recovery, complete refresh, and snapshot privacy |
| `legacy/exp3_communication/` | Resource models, sweeps, and complete-refresh cost comparisons |
| `legacy/appendix_a_libra_rank/` | Uniform-degree separable-mask ranks |

The integrated scripts are:

| Script | Checks or figure |
|---|---|
| `legacy/exp2_barrier/verify_complete_refresh.py` | Exact sampler distributions, cross-epoch attack, conditioning, adaptive snapshots, and lifted ranks |
| `legacy/exp2_barrier/check_prefix_snapshots.py` | Joint public-record/snapshot distributions and negative cases |
| `legacy/exp2_barrier/make_fig_epochs.py` | Kernel-only recovery-epoch curves |
| `legacy/exp3_communication/check_complete_refresh_costs.py` | 98 completed-refresh budgets, comparison with 392 baseline totals, and model figures |

After a full run, these scripts can also be executed individually with
`python <script path>` from the bundle root. The sampler and cost scripts require
the full baseline data; reduced sweeps are insufficient for the cost comparison.

## Generated outputs

| Location | Contents |
|---|---|
| `results/` | Stage logs and overall status in `summary.json` |
| `legacy/validation/` | Baseline logs and hash manifest |
| Each baseline module's `results/` and `plots/` | Baseline CSV/JSON data and figures |
| `legacy/exp2_barrier/validation/` | `paper_checks.json`, `prefix_checks.json`, and `lifted_rank.csv` |
| `legacy/exp2_barrier/figures/` | `epochs_to_recovery.pdf` and `.png` |
| `legacy/exp3_communication/validation/` | `completed_costs.csv` and `completed_cost_checks.json` |
| `legacy/exp3_communication/figures/` | `refresh_dimensions` and `completed_cost` figures in PDF/PNG |

Output directories and the local virtual environment are ignored by Git.
The source release contains the scripts, dependencies, and documentation;
generated outputs are recreated by the runner. Subsequent runs overwrite them.

## Scope

These experiments check exact finite-field algebra, ideal passive snapshots,
and declared resource models. They do not implement a malicious mobile
distributed service or measure network performance. See `PROVENANCE.md` for origins.
