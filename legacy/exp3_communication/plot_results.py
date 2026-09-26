"""Plot protocol totals with V3 figure numbering; PDFs plus PNGs for review."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABELS = {
    "naive": "Naive", "dpss_model": "DPSS model",
    "prss_local": "PRSS local (no seed cost)",
    "prss_commit": "PRSS commit (no seed cost)",
    "prss_dispute": "PRSS dispute (no seed cost)",
    "prss_commit_seed_dpss": "PRSS commit + DPSS seeds (S=M)",
    "full_mask": "Full mask", "kernel_mask": "Kernel mask",
}


def select(rows, **filters):
    return [r for r in rows if all(str(r[k]) == str(v) for k, v in filters.items())]


def plot_lines(rows, out, name, x, lines, title, y="communication_value",
               ylabel="Field elements per party / protocol", log=True):
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for label, filters in lines:
        values = sorted(select(rows, **filters), key=lambda r: int(r[x]))
        if not values:
            raise ValueError(f"No data for {name}: {filters}")
        xs = [int(r[x]) for r in values]
        if len(xs) != len(set(xs)):
            raise ValueError(f"Ambiguous series in {name}: {filters}")
        ax.plot(xs, [float(r[y]) for r in values], marker="o", markersize=4, label=label)
    ax.set_xlabel("Parties M" if x == "M" else "Sumcheck variables n")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log:
        ax.set_yscale("log")
    ax.grid(True, alpha=0.25, which="both")
    ax.legend(fontsize=8)
    fig.text(0.5, 0.015, "Normalized accounting; no network fanout or initial setup.",
             ha="center", fontsize=8, color="0.35")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{name}.{ext}", dpi=150)
    plt.close(fig)


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(here / "results/communication_totals.csv"))
    ap.add_argument("--outdir", default=str(here / "plots"))
    ap.add_argument("--fixed-n", type=int, default=8)
    ap.add_argument("--fixed-M", type=int, default=9)
    args = ap.parse_args()
    with open(args.csv) as f:
        rows = list(csv.DictReader(f))
    out = Path(args.outdir)
    out.mkdir(exist_ok=True, parents=True)
    pp = {"accounting_scope": "per_party", "boundary_policy": "fold_after"}
    def line(scheme, **extra):
        return (LABELS[scheme], {**pp, "scheme": scheme, "seed_state_model": "none", **extra})
    plot_lines(rows, out, "fig6_1_overhead_vs_M", "M",
               [line(s, n=args.fixed_n) for s in ("naive", "dpss_model")],
               f"Naive vs DPSS: sum over k=1,...,n-1 (n={args.fixed_n})")
    plot_lines(rows, out, "fig6_2_overhead_vs_n", "n",
               [line(s, M=args.fixed_M) for s in ("dpss_model", "prss_commit")],
               f"DPSS vs PRSS commit: protocol totals (M={args.fixed_M})")
    plot_lines(rows, out, "fig6_3_prss_seed_refresh", "n",
               [line("prss_commit", M=args.fixed_M),
                line("prss_commit_seed_dpss", M=args.fixed_M, seed_state_model="M")],
               f"PRSS seed-refresh cost: S=M at every boundary (M={args.fixed_M})")
    plot_lines(rows, out, "fig6_4_full_vs_kernel", "n",
               [line(s, M=args.fixed_M) for s in ("full_mask", "kernel_mask")],
               f"Mask-only refresh: sum over k=1,...,n-1 (M={args.fixed_M})", log=False)
    plot_lines(rows, out, "fig6_5_overhead_ratio", "n",
               [line(s, M=args.fixed_M) for s in ("naive", "dpss_model", "prss_commit")] +
               [line("prss_commit_seed_dpss", M=args.fixed_M, seed_state_model="M")],
               f"Protocol refresh cost / LXYY online verification (M={args.fixed_M})",
               y="overhead_ratio", ylabel="Refresh total / (4n+6)")
    plot_lines(rows, out, "appendix_a1_prss_profiles", "M",
               [line(s, n=args.fixed_n) for s in ("prss_local", "prss_commit", "prss_dispute")],
               f"PRSS profile sensitivity: seed cost excluded (n={args.fixed_n})")
    plot_lines(rows, out, "appendix_a2_boundary_policy", "n",
               [(f"{LABELS[s]}, {policy}", {**line(s, M=args.fixed_M)[1],
                 "boundary_policy": policy}) for s in ("naive", "dpss_model")
                for policy in ("fold_after", "fold_before")],
               f"Boundary sensitivity: after 1..n-1 vs before 0..n-2 (M={args.fixed_M})")
    plot_lines(rows, out, "appendix_a3_accounting_scope", "M",
               [(f"{LABELS[s]}, {scope}", {**line(s, n=args.fixed_n)[1],
                 "accounting_scope": scope}) for s in ("naive", "dpss_model")
                for scope in ("per_party", "total")],
               f"Per-party vs all-party protocol communication (n={args.fixed_n})",
               ylabel="Field elements / protocol (scope in legend)")
    plot_lines(rows, out, "appendix_a4_seed_sensitivity", "M",
               [(f"{carrier.upper()} seeds, S={seed_label}", {
                   **pp, "n": args.fixed_n, "scheme": "prss_commit_seed_" + carrier,
                   "seed_state_model": seed})
                for carrier in ("dpss", "naive")
                for seed, seed_label in (("one", "1"), ("M", "M"), ("M_squared", "M^2"))],
               f"PRSS commit + seed refresh: explicit size scenarios (n={args.fixed_n})")
    print("Plots: 5 main + 4 sensitivity figures, PDF and PNG")


if __name__ == "__main__":
    main()

