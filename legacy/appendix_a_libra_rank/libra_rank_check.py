"""Independent Libra sumcheck-mask rank sweep (Section 4.1, degree 2)."""
import argparse
import csv
import datetime
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crypto_core.primes import PRIMES
from crypto_core.modular_rank import rank
from appendix_a_libra_rank.construction import build_libra_constraints

DEFAULT_NS = [3, 5, 7]
DEFAULT_TRIALS = 3
DEFAULT_SEED = 20250502
SOURCE = "https://www.cs.yale.edu/homes/cpap/published/libra-crypto19.pdf"


def run(ns, trials, seed, primes, degree=2):
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rng = random.Random(seed)
    passed = 0
    failed = 0
    skipped = []
    fields = ["n", "degree", "prime_label", "prime_value", "trial_id",
              "challenge_policy", "k", "observed_rank", "expected_rank",
              "residual_dimension", "expected_residual_dimension", "pass"]
    with (out / "libra_rank_table.csv").open("w", newline="") as f, (
            out / "challenges.jsonl").open("w") as challenges_file:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for n in ns:
            for label, p in primes:
                if p == 2 or degree >= p:
                    skipped.append({"n": n, "prime_label": label, "reason": "need odd p > degree"})
                    continue
                for policy in ("exclude_01", "forced_01"):
                    for trial in range(trials):
                        r = [rng.randrange(2, p) if policy == "exclude_01"
                             else rng.randrange(2) for _ in range(n)]
                        trial_id = f"libra-{n}-{label}-{policy}-{trial}"
                        challenges_file.write(json.dumps({
                            "trial_id": trial_id, "challenges": r,
                            "prime_value": str(p), "degree": degree}) + "\n")
                        for k in range(n+1):
                            C = build_libra_constraints(n, k, r, p, degree)
                            observed = rank(C, p)
                            expected = 1 + degree*k
                            ok = observed == expected
                            writer.writerow({
                                "n": n, "degree": degree, "prime_label": label,
                                "prime_value": str(p), "trial_id": trial_id,
                                "challenge_policy": policy, "k": k,
                                "observed_rank": observed, "expected_rank": expected,
                                "residual_dimension": 1+n*degree-observed,
                                "expected_residual_dimension": degree*(n-k), "pass": int(ok)})
                            passed += int(ok)
                            if not ok:
                                failed += 1
                                (out / "failure.json").write_text(json.dumps({
                                    "trial_id": trial_id, "k": k, "matrix": C, "challenges": r}))
                                raise AssertionError(f"Libra mismatch: {trial_id}, k={k}")
    (out / "metadata.json").write_text(json.dumps({
        "config": {"ns": ns, "trials": trials, "seed": seed, "degree": degree,
                   "primes": [label for label, _ in primes],
                   "policies": ["exclude_01", "forced_01"]},
        "source": SOURCE, "source_section": "4.1, Construction 1",
        "rank_prediction": "1 + degree*k, including k=n",
        "pass_total": passed, "fail_total": failed, "skipped": skipped,
        "started_utc": started,
        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }, indent=2) + "\n")
    print(f"Libra: pass={passed}, fail={failed}, skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", type=int, nargs="+", default=DEFAULT_NS)
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--degree", type=int, default=2)
    args = ap.parse_args()
    sys.exit(run(args.ns, args.trials, args.seed, PRIMES, args.degree))

