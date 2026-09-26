"""V3 normalized field-element accounting, with explicit seed-size scenarios."""
import argparse
import csv
import datetime
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crypto_core.primes import PRIME_MERSENNE_61
from exp3_communication.state_size import d_k_table, d_k_mask, d_k_full
from exp3_communication.lxyy_baseline import lxyy_verify_per_party
from exp3_communication.naive.naive_communication import naive_per_party
from exp3_communication.dpss.dpss_communication_model import dpss_per_party
from exp3_communication.prss.prss_profiles import prss_per_party, prss_dispute_c_online
from exp3_communication.comparisons.full_vs_kernel import refresh_boundaries
from exp3_communication.comparisons.abort_restart_estimate import abort_restart_summary

DEFAULT_MS = [3, 5, 7, 9, 15, 31, 63]
DEFAULT_NS = [2, 4, 6, 8, 10, 12, 14]
BASELINE_MODEL = "online_verify_reconstruction_units"


def scenarios(M, D, full_dim, kernel_dim):
    for scheme, dim, cost in (
        ("naive", D, naive_per_party(M, D)),
        ("dpss_model", D, dpss_per_party(M, D)),
        ("full_mask", full_dim, naive_per_party(M, full_dim)),
        ("kernel_mask", kernel_dim, naive_per_party(M, kernel_dim)),
    ):
        yield scheme, "n/a", "none", "none", 0, dim, cost, 0
    for profile, co in (("local", 0), ("commit", 1),
                        ("dispute", prss_dispute_c_online(M))):
        online = prss_per_party(M, D, co)
        yield "prss_" + profile, profile, "none", "none", 0, D, online, 0
        for seed_model, S in (("one", 1), ("M", M), ("M_squared", M*M)):
            for carrier, fn in (("dpss", dpss_per_party), ("naive", naive_per_party)):
                yield ("prss_" + profile + "_seed_" + carrier, profile,
                       carrier, seed_model, S, D, online, fn(M, S))


def protocol_rows(M, n, policy, prime_label, prime_value):
    K = refresh_boundaries(n, policy)
    baseline = lxyy_verify_per_party(n)
    for k in K:
        table, mask = d_k_table(n, k), d_k_mask(n, k)
        for scheme, profile, carrier, seed_model, S, dim, online, seeds in scenarios(
                M, table + mask, d_k_full(n), mask):
            pp = online + seeds
            for scope in ("per_party", "total"):
                factor = M if scope == "total" else 1
                yield {
                    "M": M, "n": n, "k": k, "prime_label": prime_label,
                    "prime_value": str(prime_value), "scheme": scheme,
                    "profile": profile, "accounting_scope": scope,
                    "boundary_policy": policy, "K_refresh_start": K[0],
                    "K_refresh_end": K[-1], "d_k_table": table,
                    "d_k_mask": mask, "d_k_total": table + mask,
                    "refreshed_state_elements": dim,
                    "seed_refresh_model": carrier, "seed_state_model": seed_model,
                    "seed_state_elements": S, "online_comm_per_party": online,
                    "seed_refresh_per_party": seeds,
                    "comm_per_party": pp, "comm_total": M * pp,
                    "communication_value": factor * pp,
                    "lxyy_baseline_model": BASELINE_MODEL,
                    "baseline_value": factor * baseline,
                    "overhead_ratio": pp / baseline,
                }


def summarize(rows):
    groups = defaultdict(list)
    keys = ("M", "n", "scheme", "profile", "accounting_scope",
            "boundary_policy", "seed_refresh_model", "seed_state_model")
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    totals = []
    fields = ("refreshed_state_elements", "online_comm_per_party",
              "seed_refresh_per_party", "comm_per_party", "comm_total",
              "communication_value")
    for group in groups.values():
        total = dict(group[0])
        for key in ("k", "d_k_table", "d_k_mask", "d_k_total"):
            del total[key]
        total["refresh_count"] = len(group)
        for field in fields:
            total[field] = sum(row[field] for row in group)
        total["overhead_ratio"] = total["communication_value"] / total["baseline_value"]
        totals.append(total)
    return totals


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(Ms, ns, prime_label, prime_value):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    rows = [row for n in ns for M in Ms
            for policy in ("fold_after", "fold_before")
            for row in protocol_rows(M, n, policy, prime_label, prime_value)]
    totals = summarize(rows)
    write_csv(out / "communication_benchmark.csv", rows)
    write_csv(out / "communication_totals.csv", totals)
    abort_rows = []
    for n in ns:
        for M in Ms:
            for k, rc, pc, ratio in abort_restart_summary(n, refresh_boundaries(n, "fold_after")):
                abort_rows.append({
                    "n": n, "M": M, "restart_round_k": k, "restart_cost": rc,
                    "prefix_cost": pc, "baseline_lxyy": lxyy_verify_per_party(n),
                    "restart_ratio": rc / lxyy_verify_per_party(n),
                    "prefix_over_restart": ratio, "restart_cost_total": M * rc,
                    "cost_model": "verification_only_4_units_per_ordinary_round",
                })
    write_csv(out / "abort_restart.csv", abort_rows)
    meta = {
        "config": {"Ms": Ms, "ns": ns, "prime_label": prime_label,
                   "prime_value": str(prime_value), "boundary_policies": ["fold_after", "fold_before"],
                   "seed_state_models": {"one": 1, "M": "M", "M_squared": "M^2"},
                   "main_seed_state_model": "M",
                   "seed_refresh_frequency": "every_refresh_boundary"},
        "rows_written": len(rows), "protocol_totals_written": len(totals),
        "abort_rows_written": len(abort_rows), "started_utc": started,
        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "accounting": "Normalized field-element model, not network or runtime measurements",
        "exclusions": ["initial setup", "broadcast fanout", "unspecified O(1) fresh randomness"],
        "seed_assumption": "S is a scenario parameter, not a derived PRSS key count",
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Communication: {len(rows)} round rows; {len(totals)} protocol totals; "
          f"{len(abort_rows)} abort rows")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ms", type=int, nargs="+", default=DEFAULT_MS)
    ap.add_argument("--ns", type=int, nargs="+", default=DEFAULT_NS)
    ap.add_argument("--prime-label", default="PRIME_MERSENNE_61")
    ap.add_argument("--prime-value", type=int, default=PRIME_MERSENNE_61)
    args = ap.parse_args()
    sys.exit(run(args.Ms, args.ns, args.prime_label, args.prime_value))

