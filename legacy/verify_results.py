"""Check generated experiment outputs and record hashes for this run."""
import csv
import hashlib
import json
import math
import platform
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_csv(module, name):
    with (ROOT / module / "results" / name).open() as f:
        rows = list(csv.DictReader(f))
    assert rows, f"empty CSV: {name}"
    return rows


def main():
    counts = {}
    for module, name in (
        ("exp1_rank_saturation", "rank_table_multi_prime.csv"),
        ("exp2_barrier", "barrier_table.csv"),
        ("exp2_barrier", "one_more_exposure.csv"),
        ("appendix_a_libra_rank", "libra_rank_table.csv"),
    ):
        rows = read_csv(module, name)
        assert all(r["pass"] == "1" for r in rows), f"failed checks in {name}"
        counts[name] = len(rows)

    rank_rows = read_csv("exp1_rank_saturation", "rank_table_multi_prime.csv")
    meta = json.loads((ROOT / "exp1_rank_saturation/results/metadata.json").read_text())
    cfg = meta["config"]
    assert len(rank_rows) == sum(n+1 for n in cfg["ns"])*len(cfg["primes"])*cfg["trials"]*len(cfg["modes"])
    by_trial = defaultdict(list)
    for r in rank_rows:
        by_trial[r["trial_id"]].append(r)
        n, k = int(r["n"]), int(r["k"])
        assert int(r["observed_rank"]) == (1+3*k if k < n else 3*n+3)
    challenge_lines = (ROOT / "exp1_rank_saturation/results/challenges.jsonl").read_text().splitlines()
    assert len(challenge_lines) == len(by_trial)
    for line in challenge_lines:
        trial = json.loads(line)
        canonical = json.dumps({
            "n": trial["n"], "prime_label": trial["prime_label"],
            "policy": trial["challenge_policy"], "challenges": trial["challenges"]
        }, sort_keys=True).encode()
        digest = "sha256:" + hashlib.sha256(canonical).hexdigest()
        assert digest == trial["challenge_digest"]
        group = sorted(by_trial[trial["trial_id"]], key=lambda r: int(r["k"]))
        assert len(group) == trial["n"]+1
        assert all(r["challenge_digest"] == digest for r in group)
        assert [int(r["observed_rank"]) for r in group] == trial["observed_rank_seq"]

    libra = read_csv("appendix_a_libra_rank", "libra_rank_table.csv")
    libmeta = json.loads((ROOT / "appendix_a_libra_rank/results/metadata.json").read_text())
    cfg = libmeta["config"]
    expected_libra = sum(n+1 for n in cfg["ns"])*cfg["trials"]*len(cfg["policies"])*(
        len(cfg["primes"]))
    if not libmeta["skipped"]:
        assert len(libra) == expected_libra
    for r in libra:
        assert int(r["observed_rank"]) == 1+int(r["degree"])*int(r["k"])
        assert int(r["residual_dimension"]) == int(r["degree"])*(int(r["n"])-int(r["k"]))

    rounds = read_csv("exp3_communication", "communication_benchmark.csv")
    totals = read_csv("exp3_communication", "communication_totals.csv")
    commmeta = json.loads((ROOT / "exp3_communication/results/metadata.json").read_text())
    cfg = commmeta["config"]
    # 7 seed-excluded comparators + 3 profiles * 3 seed sizes * 2 carriers.
    scenario_count = 7 + 3*3*2
    assert len(rounds) == sum(n-1 for n in cfg["ns"])*len(cfg["Ms"])*4*scenario_count
    assert len(totals) == len(cfg["ns"])*len(cfg["Ms"])*4*scenario_count
    keys = ("M", "n", "scheme", "accounting_scope", "boundary_policy", "seed_state_model")
    grouped = defaultdict(list)
    for r in rounds:
        grouped[tuple(r[k] for k in keys)].append(r)
    assert len(totals) == len(grouped)
    seen = set()
    for r in totals:
        key = tuple(r[k] for k in keys)
        assert key not in seen
        seen.add(key)
        group = grouped[key]
        M, n = int(r["M"]), int(r["n"])
        K = list(range(1, n)) if r["boundary_policy"] == "fold_after" else list(range(n-1))
        assert sorted(int(x["k"]) for x in group) == K
        assert int(r["refresh_count"]) == n-1
        pp = sum(int(x["comm_per_party"]) for x in group)
        assert pp == int(r["comm_per_party"])
        assert int(r["comm_total"]) == M*pp
        factor = M if r["accounting_scope"] == "total" else 1
        assert int(r["communication_value"]) == factor*pp
        assert int(r["baseline_value"]) == factor*(4*n+6)
        assert math.isclose(float(r["overhead_ratio"]), pp/(4*n+6), rel_tol=1e-12)
        if r["boundary_policy"] == "fold_after":
            D = 2**(n+1)-4 + 3*n*(n-1)//2 + 2*(n-1)
            if r["scheme"] == "naive":
                assert pp == D*(M-1)
            if r["scheme"] == "dpss_model":
                assert pp == D+(n-1)*M*M
            if r["scheme"] == "full_mask":
                assert pp == (n-1)*(3*n+3)*(M-1)
            if r["scheme"] == "kernel_mask":
                assert pp == (3*n*(n-1)//2+2*(n-1))*(M-1)
    counts["communication_benchmark.csv"] = len(rounds)
    counts["communication_totals.csv"] = len(totals)
    counts["abort_restart.csv"] = len(read_csv("exp3_communication", "abort_restart.csv"))
    expected_plots = ["fig6_1_overhead_vs_M", "fig6_2_overhead_vs_n",
                      "fig6_3_prss_seed_refresh", "fig6_4_full_vs_kernel",
                      "fig6_5_overhead_ratio", "appendix_a1_prss_profiles",
                      "appendix_a2_boundary_policy", "appendix_a3_accounting_scope",
                      "appendix_a4_seed_sensitivity"]
    for name in expected_plots:
        pdf = ROOT / "exp3_communication/plots" / (name + ".pdf")
        assert pdf.stat().st_size > 1000 and pdf.read_bytes().startswith(b"%PDF")
        assert pdf.with_suffix(".png").stat().st_size > 1000

    files = sorted(p for module in ("crypto_core", "exp1_rank_saturation", "exp2_barrier",
                                   "exp3_communication", "appendix_a_libra_rank")
                   for p in (ROOT / module).rglob("*")
                   if p.is_file() and p.suffix in (".py", ".csv", ".json", ".jsonl", ".pdf", ".png"))
    files += [ROOT / name for name in ("run_all.py", "verify_results.py", "requirements.txt",
                                      "requirements-wsl.lock.txt", "README.md")]
    manifest = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(), "executable": sys.executable,
        "csv_rows": counts, "exp1_trials": len(by_trial), "plots": len(expected_plots),
        "status": "PASS",
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    import matplotlib
    manifest["matplotlib"] = matplotlib.__version__
    (ROOT / "validation/run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(counts, indent=2))
    print("PASS: coverage, challenges, ranks, boundary sums, closed forms, plot files, hashes")


if __name__ == "__main__":
    main()
