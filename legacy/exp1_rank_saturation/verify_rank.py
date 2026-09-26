"""
Experiment 1: Mask Rank Saturation Verification.
V3 spec (see experiment_plan_v3 §三):

  - main mode  : challenge_policy in {include_01, exclude_01}
                 follows the LaTeX Lemma 4.4 statement
  - stress mode: challenge_policy = forced_01  (r_j sampled from {0, 1})
                 NOT required to PASS; records observed_rank vs expected_rank

  Outputs:
    results/rank_table_multi_prime.csv   (main + stress both written here)
    results/challenges.jsonl             (full challenge vectors per trial)
    debug/C_{n}_{trial}_{k}.csv          (mismatch dumps; main mode only)
    debug/r_{n}_{trial}.csv              (mismatch challenge dumps)
    metadata.json                        (run config + summary)

  CSV schema (V3 §3.5):
    n, prime_label, prime_value, trial_id, challenge_policy,
    challenge_digest, degenerate_challenge_count,
    k, observed_rank, expected_rank, pass

Usage:
  python verify_rank.py                       # main mode (include_01 by default)
  python verify_rank.py --mode stress         # stress mode only
  python verify_rank.py --mode both           # main + stress
  python verify_rank.py --policy exclude_01   # main with r_j sampled from F_p \\ {0,1}
"""

import os
import sys
import csv
import json
import hashlib
import argparse
import random
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crypto_core.primes import PRIMES
from crypto_core import modular_rank as MR
from exp1_rank_saturation.construction import (
    build_C_k, expected_rank, gamma_dim, is_degenerate_challenge
)


# -------- defaults --------

DEFAULT_NS = [2, 3, 4, 5, 6, 8, 10, 12]
DEFAULT_TRIALS = 5
DEFAULT_SEED = 20250502


def _outdir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


# -------- challenge sampling --------

def sample_challenges(n: int, p: int, policy: str, rng: random.Random):
    """
    Draw n challenges r_1, ..., r_n in F_p following `policy`:
      - include_01 : uniform over [0, p)
      - exclude_01 : uniform over [0, p) but resampled if in {0, 1}
      - forced_01  : uniform over {0, 1}
    """
    if policy == "include_01":
        return [rng.randrange(p) for _ in range(n)]
    if policy == "exclude_01":
        out = []
        while len(out) < n:
            r = rng.randrange(p)
            if r not in (0, 1):
                out.append(r)
        return out
    if policy == "forced_01":
        if p < 2:
            raise ValueError("forced_01 needs p >= 2")
        return [rng.randrange(2) for _ in range(n)]
    raise ValueError(f"unknown policy: {policy}")


def challenge_digest(challenges, prime_label: str, n: int, policy: str) -> str:
    """sha256 over a canonical encoding of the challenge vector."""
    canonical = json.dumps({
        "n": n, "prime_label": prime_label, "policy": policy,
        "challenges": [int(x) for x in challenges],
    }, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


# -------- main runner --------

def dump_C_and_r(n, trial_id, k, C, r, p):
    debug_dir = os.path.join(_outdir(), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    cpath = os.path.join(debug_dir, f"C_{n}_{trial_id}_{k}.csv")
    rpath = os.path.join(debug_dir, f"r_{n}_{trial_id}.csv")
    with open(cpath, "w", newline="") as f:
        w = csv.writer(f)
        for row in C:
            w.writerow([str(x) for x in row])
    with open(rpath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([str(x) for x in r])
    return cpath, rpath


def run_one_trial(n, prime_label, p, trial_id, policy, rng,
                  csv_writer, jsonl_handle, halt_on_fail=True):
    """
    Run one trial: sample n challenges, then for k = 0..n compute rank(C_k),
    write CSV rows, append jsonl line. Return (pass_count, fail_count).

    halt_on_fail=True -> on mismatch, dump and return (..., 1, abort=True)
    """
    challenges = sample_challenges(n, p, policy, rng)
    digest = challenge_digest(challenges, prime_label, n, policy)
    degen_count = sum(1 for r in challenges if is_degenerate_challenge(r, p))

    obs_seq = []
    pass_count = 0
    fail_count = 0
    abort = False

    for k in range(n + 1):
        C = build_C_k(n, k, challenges[:k], p)
        observed = MR.rank(C, p)
        expected = expected_rank(k, n)
        observed_pass = (observed == expected)

        # In stress mode, "pass" just means we recorded the value;
        # but we still emit the boolean for downstream analysis.
        csv_writer.writerow({
            "n": n,
            "prime_label": prime_label,
            "prime_value": str(p),
            "trial_id": trial_id,
            "challenge_policy": policy,
            "challenge_digest": digest,
            "degenerate_challenge_count": degen_count,
            "k": k,
            "observed_rank": observed,
            "expected_rank": expected,
            "pass": int(observed_pass),
        })
        obs_seq.append(observed)

        if observed_pass:
            pass_count += 1
        else:
            fail_count += 1
            if policy != "forced_01" and halt_on_fail:
                # Main-mode mismatch: dump and abort
                cpath, rpath = dump_C_and_r(n, trial_id, k, C, challenges, p)
                print(f"  [FAIL] n={n} prime={prime_label} trial={trial_id} "
                      f"policy={policy} k={k}: observed={observed} expected={expected}")
                print(f"         dumped {cpath}")
                print(f"         dumped {rpath}")
                abort = True
                break

    jsonl_handle.write(json.dumps({
        "n": n, "prime_label": prime_label, "prime_value": str(p),
        "trial_id": trial_id, "challenge_policy": policy,
        "challenges": [int(x) for x in challenges],
        "challenge_digest": digest,
        "degenerate_challenge_count": degen_count,
        "observed_rank_seq": obs_seq,
    }) + "\n")
    jsonl_handle.flush()

    return pass_count, fail_count, abort


def run(modes, ns, primes, trials, seed, main_policy):
    """
    Run rank-saturation verification across (mode, n, prime, trial).

    modes: list of tags from {"main", "stress"}
    """
    out = _outdir()
    csv_path = os.path.join(out, "results", "rank_table_multi_prime.csv")
    jsonl_path = os.path.join(out, "results", "challenges.jsonl")
    meta_path = os.path.join(out, "results", "metadata.json")
    os.makedirs(os.path.join(out, "results"), exist_ok=True)

    schema = [
        "n", "prime_label", "prime_value", "trial_id",
        "challenge_policy", "challenge_digest", "degenerate_challenge_count",
        "k", "observed_rank", "expected_rank", "pass"
    ]

    summary = {
        "config": {
            "modes": modes, "ns": ns, "trials": trials, "seed": seed,
            "main_policy": main_policy,
            "primes": [lbl for (lbl, _) in primes],
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "totals": {},
        "main_mode": {"pass_total": 0, "fail_total": 0, "aborted": False},
        "stress_mode": {"pass_total": 0, "fail_total": 0, "aborted": False},
    }

    with open(csv_path, "w", newline="") as fcsv, open(jsonl_path, "w") as fjsonl:
        writer = csv.DictWriter(fcsv, fieldnames=schema)
        writer.writeheader()
        rng = random.Random(seed)

        for mode in modes:
            policy = main_policy if mode == "main" else "forced_01"
            print(f"\n=== mode={mode}  policy={policy} ===")
            for n in ns:
                for prime_label, p in primes:
                    # Coefficient constraints need odd characteristic only;
                    # challenges may repeat and n is not bounded by p.
                    for trial in range(trials):
                        trial_id = f"{mode}-{n}-{prime_label}-t{trial}"
                        pc, fc, aborted = run_one_trial(
                            n, prime_label, p, trial_id, policy, rng,
                            writer, fjsonl,
                            halt_on_fail=(mode == "main"),
                        )
                        bucket = summary["main_mode" if mode == "main" else "stress_mode"]
                        bucket["pass_total"] += pc
                        bucket["fail_total"] += fc
                        if aborted:
                            bucket["aborted"] = True
                            print(f"  ABORT: main mode mismatch detected; halting.")
                            summary["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                            with open(meta_path, "w") as fm:
                                json.dump(summary, fm, indent=2)
                            return 1
                        print(f"  n={n:>2} prime={prime_label:<18} trial={trial}  "
                              f"pass={pc:>2}/{pc+fc}")

    summary["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(meta_path, "w") as fm:
        json.dump(summary, fm, indent=2)
    print(f"\nresults: {csv_path}")
    print(f"jsonl  : {jsonl_path}")
    print(f"summary: {meta_path}")
    print(f"main:   pass={summary['main_mode']['pass_total']} "
          f"fail={summary['main_mode']['fail_total']}  "
          f"aborted={summary['main_mode']['aborted']}")
    print(f"stress: pass={summary['stress_mode']['pass_total']} "
          f"fail={summary['stress_mode']['fail_total']}")
    return 0 if summary["main_mode"]["fail_total"] == 0 else 1


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["main", "stress", "both"], default="both")
    ap.add_argument("--policy", choices=["include_01", "exclude_01"], default="include_01",
                    help="challenge policy for main mode (V3 sign-off pending Lemma 4.4 statement)")
    ap.add_argument("--ns", type=int, nargs="+", default=DEFAULT_NS)
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.mode == "both":
        modes = ["main", "stress"]
    else:
        modes = [args.mode]
    rc = run(modes, args.ns, PRIMES, args.trials, args.seed, args.policy)
    sys.exit(rc)
