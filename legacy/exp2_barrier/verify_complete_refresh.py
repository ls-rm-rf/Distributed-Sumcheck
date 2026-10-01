"""Exact complete-refresh, cross-epoch, and passive-snapshot checks."""
import csv
import hashlib
import itertools
import json
import platform
import sys
from collections import Counter
from pathlib import Path

if not __debug__:
    raise SystemExit("Run without -O: exact checks require assertions.")

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
sys.path.insert(0, str(EXPERIMENTS))
from crypto_core.modular_rank import kernel_basis, rank, rref
from exp1_rank_saturation.construction import build_C_k


def complement(C, d, p):
    B = kernel_basis(C, p, cols=d)
    _, pivots = rref(C, p)
    E = [[int(i == j) for i in range(d)] for j in pivots]
    assert rank(B + E, p) == d
    assert all(sum(a*b for a, b in zip(row, v)) % p == 0 for row in C for v in B)
    return B, E


def lincomb(vectors, weights, d, p):
    return tuple(sum(w*v[j] for w, v in zip(weights, vectors)) % p for j in range(d))


def exhaustive_lift():
    cases = [(3, [], 2), (3, [[1, 0]], 2), (3, [[1, 0], [0, 1]], 2),
             (5, [[1, 1]], 2)]
    results = []
    for p, C, d in cases:
        B, E = complement(C, d, p)
        r = len(B)
        outcomes = Counter()
        for seed in itertools.product(range(p), repeat=r+d):
            constant = lincomb(B, seed[:r], d, p)
            slope = lincomb(B + E, seed[r:], d, p)
            outcomes[constant+slope] += 1
        # Independent enumeration of every admissible coefficient vector.
        allowed = {v for v in itertools.product(range(p), repeat=2*d)
                   if all(sum(a*b for a, b in zip(row, v[:d])) % p == 0 for row in C)}
        assert set(outcomes) == allowed
        assert set(outcomes.values()) == {1}
        constants = Counter()
        for coefficients, frequency in outcomes.items():
            constants[coefficients[:d]] += frequency
        assert len(constants) == p**r
        assert set(constants.values()) == {p**d}  # t=1; dt symbols given D(0).
        results.append({"p": p, "C": C, "d": d, "t": 1,
                        "outputs": len(outcomes), "seed_symbols": r+d, "uniform": True,
                        "semantic_values": len(constants),
                        "outputs_per_semantic_value": p**d,
                        "dealer_randomness_symbols": d})
    return results


def mobile_view(p, secret, repaired):
    # C=[1,0], t=1. Expose party 1 before and party 2 after a boundary.
    # B=(0,1), E=(1,0); the second semantic coordinate initially equals zero.
    views = Counter()
    for a, b, u0, u1 in itertools.product(range(p), repeat=4):
        for z1 in (range(p) if repaired else (0,)):
            old = ((secret+a) % p, b)
            new = ((secret+2*(a+z1)) % p, (u0+2*(b+u1)) % p)
            views[old+new] += 1
    return views


def check_mobile():
    p = 5
    old = [mobile_view(p, s, False) for s in range(p)]
    new = [mobile_view(p, s, True) for s in range(p)]
    assert all(new[s] == new[0] for s in range(p))
    assert all(set(old[s]).isdisjoint(old[j]) for s in range(p) for j in range(s))
    for s, views in enumerate(old):
        assert all((2*v[0]-v[2]) % p == s for v in views)
    return {"p": p, "secrets": p, "observations_per_epoch": 1,
            "kernel_only_supports_disjoint": True, "completed_views_identical": True,
            "kernel_only_views_per_secret": len(old[0]), "completed_views_per_secret": len(new[0]),
            "samples_per_secret_completed": sum(new[0].values())}


def check_lxyy():
    rows = []
    for p in (3, 2**61-1):
        for n in (2, 3, 5, 8):
            for k in range(n+1):
                d, t = 3*n+3, 2
                C = build_C_k(n, k, [i % 2 for i in range(k)], p)
                B, E = complement(C, d, p)
                r = len(B)
                explicit = []
                for coordinate in range(1+3*k, d) if k < n else ():
                    v = [0]*d
                    v[0], v[coordinate] = -pow(2, -1, p) % p, 1
                    explicit.append(v)
                assert len(explicit) == r and rank(explicit, p) == r
                assert all(sum(a*b for a, b in zip(row, v)) % p == 0
                           for row in C for v in explicit)
                expected = 3*(n-k)+2 if k < n else 0
                assert r == expected
                lifted = [v+[0]*(d*t) for v in B]
                for ell in range(1, t+1):
                    lifted.extend([[0]*(d*ell)+v+[0]*(d*(t-ell)) for v in B+E])
                actual = rank(lifted, p)
                assert actual == r+d*t
                rows.append({"p": p, "n": n, "k": k, "d": d, "t": t,
                             "r": r, "zero_sharing_coordinates": len(E),
                             "lifted_rank": actual, "expected": r+d*t})
    return rows


def check_conditioning():
    # Marginal independence does not justify conditioning on a joint history.
    p = 3
    delta_history = Counter()
    refreshed_given_history = [Counter() for _ in range(p)]
    valid_history = [Counter() for _ in range(p)]
    for old, delta in itertools.product(range(p), repeat=2):
        history = (old+delta) % p
        delta_history[delta, history] += 1
        refreshed_given_history[history][(old+delta) % p] += 1
        # This history precedes the fresh coins and can depend on the old state.
        valid_history[old*old % p][(old+delta) % p] += 1
    assert set(delta_history.values()) == {1}
    assert all(set(row) == {history} for history, row in enumerate(refreshed_given_history))
    assert all(len(row) == p and len(set(row.values())) == 1 for row in valid_history if row)
    return {"p": p, "marginal_independence_counterexample": True,
            "joint_freshness_restores_uniformity": True}


def check_adaptive_snapshots():
    # Two quadratic scalar sharings; query choices depend on all earlier answers.
    # M=4,t=2 tests the algebraic theorem, not an honest-majority implementation.
    p = 5
    reference = None
    for secrets in itertools.product(range(p), repeat=2):
        views = Counter()
        for coins in itertools.product(range(p), repeat=4):
            transcript = []
            for epoch, secret in enumerate(secrets):
                a, b = coins[2*epoch:2*epoch+2]
                x = 1 if epoch == 0 else 1+sum(transcript) % 4
                y = (secret+a*x+b*x*x) % p
                candidates = [i for i in range(1, 5) if i != x]
                xx = candidates[(y+sum(transcript)) % 3]
                yy = (secret+a*xx+b*xx*xx) % p
                transcript.extend((x, y, xx, yy))
            views[tuple(transcript)] += 1
        if reference is None:
            reference = views
        assert views == reference
    assert len(reference) == p**4 and set(reference.values()) == {1}
    return {"p": p, "M": 4, "t": 2, "epochs": 2, "secret_sequences": p**2,
            "samples_per_sequence": p**4, "full_view_distributions_identical": True}


def csv_write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest_path = EXPERIMENTS / "validation/run_manifest.json"
    if not manifest_path.exists():
        raise SystemExit("First run python run_experiments.py from the experiment bundle.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checked_hashes = 0
    for path, expected in manifest["sha256"].items():
        actual = hashlib.sha256((EXPERIMENTS / path).read_bytes()).hexdigest()
        assert actual == expected, path
        checked_hashes += 1
    out = HERE / "validation"
    out.mkdir(exist_ok=True)
    exhaustive = exhaustive_lift()
    mobile = check_mobile()
    conditioning = check_conditioning()
    adaptive = check_adaptive_snapshots()
    ranks = check_lxyy()
    csv_write(out / "lifted_rank.csv", ranks)
    summary = {"status": "PASS", "python": sys.version, "platform": platform.platform(),
               "exhaustive_lift": exhaustive, "mobile_snapshot": mobile,
               "conditioning_assumptions": conditioning, "adaptive_snapshots": adaptive,
               "lifted_rank_checks": len(ranks), "legacy_hashes_checked": checked_hashes,
               "legacy_csv_counts": manifest["csv_rows"],
               "scope": "Exact algebra and ideal snapshots; no network implementation"}
    (out / "paper_checks.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
