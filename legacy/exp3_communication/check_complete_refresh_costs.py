"""Complete-refresh resource counts and model figures."""
import csv
import json
from pathlib import Path

if not __debug__:
    raise SystemExit("Run without -O: exact checks require assertions.")

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent


def accounting():
    rows = []
    for M in (3, 5, 7, 9, 15, 31, 63):
        for n in (2, 4, 6, 8, 10, 12, 14):
            for policy in ("fold_after", "fold_before"):
                boundaries = range(1, n) if policy == "fold_after" else range(n-1)
                d = 3*n+3
                A = sum(2*2**(n-k) for k in boundaries)
                R = sum(3*(n-k)+2 for k in boundaries)
                Q = sum(1+3*k for k in boundaries)
                assert R+Q == d*(n-1)
                assert A == (2**(n+1)-4 if policy == "fold_after" else 2**(n+2)-8)
                assert R == ((n-1)*(3*n+4)//2 if policy == "fold_after" else (n-1)*(3*n+10)//2)
                row = {"M": M, "n": n, "policy": policy, "boundaries": n-1,
                       "table_coordinates": A, "kernel_random_coordinates": R,
                       "complement_zero_coordinates": Q, "completed_mask_coordinates": R+Q,
                       "legacy_naive": (M-1)*(A+R), "completed_naive": (M-1)*(A+R+Q),
                       "legacy_batched_model": A+R+(n-1)*M*M,
                       "completed_batched_model": A+R+Q+(n-1)*M*M,
                       "terminal_fresh_masks_excluded": 2*(n-1),
                       "baseline_reconstruction_units": 4*n+6}
                rows.append(row)
    # Compare against every available legacy table-and-kernel total in both scopes.
    lookup = {(row["M"], row["n"], row["policy"]): row for row in rows}
    checked = 0
    with (EXPERIMENTS / "exp3_communication/results/communication_totals.csv").open() as f:
        for old in csv.DictReader(f):
            if old["scheme"] not in ("naive", "dpss_model"):
                continue
            row = lookup[int(old["M"]), int(old["n"]), old["boundary_policy"]]
            key = "legacy_naive" if old["scheme"] == "naive" else "legacy_batched_model"
            factor = int(old["M"]) if old["accounting_scope"] == "total" else 1
            assert int(old["communication_value"]) == factor*row[key]
            checked += 1
    assert checked == 392
    return rows, checked


def csv_write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def figures(costs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 10, "pdf.fonttype": 42})
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(out / (name+".pdf"), bbox_inches="tight")
        fig.savefig(out / (name+".png"), dpi=170, bbox_inches="tight")
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(5.7, 3.0))
    n, t = 8, 4
    ks = list(range(n+1))
    r = [3*(n-k)+2 if k < n else 0 for k in ks]
    ax.plot(ks, r, "o-", label="Semantic increment: $r_k$")
    ax.plot(ks, [x+(3*n+3)*t for x in r], "s--", label="Full sharing increment: $r_k+dt$")
    ax.set(xlabel="Completed rounds $k$", ylabel="Dimension over the field", xticks=ks)
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
    save(fig, "refresh_dimensions")
    fig, ax = plt.subplots(figsize=(5.7, 3.0))
    selected = [x for x in costs if x["M"] == 9 and x["policy"] == "fold_after"]
    ax.plot([x["n"] for x in selected], [x["legacy_batched_model"] for x in selected],
            "o--", label="Table + kernel budget")
    ax.plot([x["n"] for x in selected], [x["completed_batched_model"] for x in selected],
            "s-", label="Table + completed sharing budget")
    ax.set(xlabel="Sumcheck variables $n$", ylabel="Normalized cost per party", yscale="log")
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
    save(fig, "completed_cost")


def main():
    if not (EXPERIMENTS / "validation/run_manifest.json").exists():
        raise SystemExit("First run python run_experiments.py from the experiment bundle.")
    out = HERE / "validation"
    out.mkdir(exist_ok=True)
    costs, compared = accounting()
    csv_write(out / "completed_costs.csv", costs)
    figures(costs)
    summary = {"status": "PASS", "cost_rows": len(costs), "legacy_totals_compared": compared,
               "scope": "Sharing resources and normalized cost models; no network timing"}
    (out / "completed_cost_checks.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
