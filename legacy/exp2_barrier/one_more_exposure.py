"""One-more post-boundary exposure, without supplying p(0) to the adversary."""
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crypto_core.primes import PRIMES
from crypto_core.modular_rank import projected_nullity
from exp2_barrier.adversary_matrix import build_adversary_matrix, d_indices
from exp2_barrier.barrier_validation import DEFAULT_MS, threshold_for_M


def evaluate(t, c, p, extra):
    rows, meta = build_adversary_matrix(t, c, p)
    if meta["secret_eq_included"]:
        rows = rows[:-1]
    if extra:
        alpha = c+1
        rows.append([pow(alpha, j, p) for j in range(t+1)] +
                    [pow(alpha, j, p) for j in range(1, t+1)])
    cols = 2*t+1
    secret = int(projected_nullity(rows, [0], p, cols=cols) == 0)
    residual = projected_nullity(rows, d_indices(t), p, cols=cols)
    return secret, residual


def run():
    out = Path(__file__).resolve().parent / "results"
    records = []
    for M in DEFAULT_MS:
        t = threshold_for_M(M)
        for label, p in PRIMES:
            if t+1 >= p:
                continue
            for c in range(t+1):
                for extra in (False, True):
                    secret, residual = evaluate(t, c, p, extra)
                    expected = int(extra and c == t)
                    row = {"M": M, "t": t, "c": c, "prime_label": label,
                           "prime_value": str(p), "secret_given": 0,
                           "extra_post_share": int(extra), "secret_recoverable": secret,
                           "expected_secret_recoverable": expected,
                           "residual_transition_dim": residual,
                           "expected_residual_dim": t-c,
                           "pass": int(secret == expected and residual == t-c)}
                    records.append(row)
                    if not row["pass"]:
                        (out / "one_more_failure.json").write_text(json.dumps(row, indent=2))
                        raise AssertionError(row)
    with (out / "one_more_exposure.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(f"One-more exposure: {len(records)} exact checks passed (no secret equation)")


if __name__ == "__main__":
    run()

