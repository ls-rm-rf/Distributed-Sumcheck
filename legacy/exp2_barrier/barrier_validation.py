"""
Experiment 2: Sharp Barrier Empirical Validation (V3 corrected version).

Tests Corollary 4.2: same-committee Shamir refresh, residual transition entropy
                     = (t - c) * log|F|

V3 §4.4-4.5 CORRECTED judgments (vs v2 errors):

    polynomial_recoverable
        v2 (WRONG): rank(M restricted to p-columns) == t+1
        v3 (RIGHT): projected_nullity(M, p_indices) == 0
                    i.e. Pi_p(ker M) == {0}

    secret_recoverable
        Same kernel-projection judgment, restricted to {p_0}:
            projected_nullity(M, [0]) == 0
        Equivalent: e_0 in rowspan(M).

    residual_transition_dim
        v2 (UNCLEAR): "project null space onto d-coords" --
                      could be misread as intersection
        v3 (PRECISE): residual_transition_dim = dim Pi_D(ker M)
                                              = projected_nullity(M, d_indices)
        NOT  dim(ker M ∩ D-coords)   (intersection -- generally different).

Theory predictions:
    c < t  : secret_recoverable = 0, polynomial_recoverable = 0,
             residual_transition_dim = t - c > 0
    c = t  : secret_recoverable = 1, polynomial_recoverable = 1,
             residual_transition_dim = 0

CSV schema (V3 §4.6):
    M, t, c, prime_label, prime_value, trial_id,
    secret_recoverable, polynomial_recoverable,
    residual_transition_dim, expected_residual_dim, pass

Usage:
    python barrier_validation.py
    python barrier_validation.py --Ms 3 5 7 --trials 5
"""

import os
import sys
import csv
import json
import argparse
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crypto_core.primes import PRIMES
from crypto_core import modular_rank as MR
from exp2_barrier.adversary_matrix import (
    build_adversary_matrix, p_indices, d_indices,
)


DEFAULT_MS = [3, 5, 7, 9]
DEFAULT_TRIALS = 10
DEFAULT_SEED = 20250502


def _outdir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def threshold_for_M(M: int) -> int:
    return (M - 1) // 2


def evaluate_one_config(M_party: int, t: int, c: int, prime_label: str, p: int):
    """
    Build M_adv and compute the three indicators.

    Returns dict with keys:
       secret_recoverable, polynomial_recoverable,
       residual_transition_dim, expected_residual_dim, pass
    """
    M_adv, meta = build_adversary_matrix(t, c, p)
    cols = 2 * t + 1   # for c=0 the matrix has zero rows; cols hint is required

    # Indicators via kernel projection (V3 corrected).
    sec_proj_dim = MR.projected_nullity(M_adv, [0], p, cols=cols)
    poly_proj_dim = MR.projected_nullity(M_adv, p_indices(t), p, cols=cols)
    resid_dim = MR.projected_nullity(M_adv, d_indices(t), p, cols=cols)

    secret_rec = int(sec_proj_dim == 0)
    poly_rec = int(poly_proj_dim == 0)
    expected_resid = t - c

    # Sanity check secret <=> e_0 in rowspan(M_adv) via stacked-rank form.
    stacked_diff = MR.stacked_rank_difference(M_adv, [0], p, cols=cols)
    # secret_recoverable iff stacking e_0 doesn't increase rank.
    secret_rec_alt = int(stacked_diff == 0)
    if secret_rec != secret_rec_alt:
        # internal sanity: should never trigger if implementations agree
        raise RuntimeError(
            f"internal mismatch on secret_recoverable @ (M={M_party}, t={t}, c={c}, p={p}): "
            f"projection={secret_rec} vs stacked_rank={secret_rec_alt}"
        )

    passed = (resid_dim == expected_resid)
    # Boundary-case check on indicators:
    if c == t:
        passed &= (secret_rec == 1) and (poly_rec == 1)
    if c < t:
        passed &= (secret_rec == 0) and (poly_rec == 0)

    return {
        "secret_given": int(meta["secret_eq_included"]),
        "secret_recoverable": secret_rec,
        "polynomial_recoverable": poly_rec,
        "residual_transition_dim": resid_dim,
        "expected_residual_dim": expected_resid,
        "pass": int(passed),
    }


def run(Ms, primes, trials, seed):
    out = _outdir()
    csv_path = os.path.join(out, "results", "barrier_table.csv")
    meta_path = os.path.join(out, "results", "metadata.json")
    os.makedirs(os.path.join(out, "results"), exist_ok=True)

    schema = [
        "M", "t", "c", "prime_label", "prime_value", "trial_id",
        "secret_recoverable", "polynomial_recoverable",
        "residual_transition_dim", "expected_residual_dim", "pass", "secret_given"
    ]

    summary = {
        "config": {
            "Ms": Ms, "trials": trials, "seed": seed,
            "primes": [lbl for (lbl, _) in primes],
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "pass_total": 0, "fail_total": 0,
        "trial_semantics": "deterministic repetitions, not independent random attacks",
        "boundary_semantics": "c=t includes p(0)=secret; recovery is conditional on this supplied equation",
        "skipped_configs": [],
        "unique_configs": 0,
    }

    failures = []

    with open(csv_path, "w", newline="") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=schema)
        writer.writeheader()

        for M_party in Ms:
            t = threshold_for_M(M_party)
            for c in range(0, t + 1):
                for prime_label, p in primes:
                    if t + 1 >= p:
                        # Need p > t+1 for distinct alpha_i
                        summary["skipped_configs"].append({"M": M_party, "t": t, "c": c,
                            "prime_label": prime_label, "reason": "matrix implementation requires p > t+1"})
                        continue
                    summary["unique_configs"] += 1
                    for trial in range(trials):
                        # NB: build_adversary_matrix is deterministic in (t, c, p)
                        # because the linear-system structure does not depend on
                        # the actual share VALUES -- only on alpha_i positions and
                        # field. We retain the trial loop for (a) future randomized
                        # variants (e.g. random alpha permutation) and (b) cleanly
                        # matching the V3 schema with trial_id column.
                        result = evaluate_one_config(M_party, t, c, prime_label, p)
                        trial_id = f"M{M_party}-t{t}-c{c}-{prime_label}-r{trial}"
                        writer.writerow({
                            "M": M_party, "t": t, "c": c,
                            "prime_label": prime_label, "prime_value": str(p),
                            "trial_id": trial_id,
                            **result,
                        })
                        if result["pass"]:
                            summary["pass_total"] += 1
                        else:
                            summary["fail_total"] += 1
                            failures.append({"M": M_party, "t": t, "c": c,
                                             "prime_label": prime_label, **result})
                            matrix, _ = build_adversary_matrix(t, c, p)
                            summary["first_failures"] = failures
                            with open(meta_path, "w") as fm:
                                json.dump(summary, fm, indent=2)
                            with open(os.path.join(out, "results", "failure_matrix.json"), "w") as fm:
                                json.dump(matrix, fm)
                            return 1

            # progress per-M
            print(f"M={M_party:>2}  t={t}  cs=0..{t}  done")

    summary["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary["first_failures"] = failures[:5]
    with open(meta_path, "w") as fm:
        json.dump(summary, fm, indent=2)

    print(f"\nresults: {csv_path}")
    print(f"summary: {meta_path}")
    print(f"pass={summary['pass_total']} fail={summary['fail_total']}")
    return 0 if summary["fail_total"] == 0 else 1


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ms", type=int, nargs="+", default=DEFAULT_MS)
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rc = run(args.Ms, PRIMES, args.trials, args.seed)
    sys.exit(rc)
