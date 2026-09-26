
中文说明：[README.zh-CN.md](README.zh-CN.md).

## Run from scratch

Use Python 3.10 or later with Matplotlib.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_experiments.py
```

`requirements.lock.txt` records the original Python 3.14.4 environment's dependency
versions. Install it instead to use those versions. WSL are not required.
After installing dependencies, no network or files outside this bundle are needed.

The runner generates all baseline data first, then runs the complete-resharing
and prefix-snapshot supplements and generates the paper figure. Failures return
a nonzero exit status. Do not use `-O` or `PYTHONOPTIMIZE`: checks use assertions.

## Code layout

| Path | Purpose |
|---|---|
| `legacy/crypto_core/` | Field, polynomial, rank, and Shamir utilities |
| `legacy/exp1_rank_saturation/` | Sparse-mask prefix ranks |
| `legacy/exp2_barrier/` | Overlap and extra-exposure checks |
| `legacy/exp3_communication/` | Resource-accounting models and sweeps |
| `legacy/appendix_a_libra_rank/` | Uniform-degree separable-mask ranks |


Execution creates data under the baseline modules' `results/` and `plots/`,
`legacy/validation/`, and the root
`results/`. These directories are ignored by Git and absent from this distribution.
Subsequent runs overwrite generated outputs. Overall status is written to
`results/summary.json`.


```


## Scope

Exact finite-field algebra, ideal snapshots, and declared resource models are
checked here, not a maliciously secure distributed service or network performance.
See `PROVENANCE.md` for origins. 
