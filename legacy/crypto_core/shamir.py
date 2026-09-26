"""
Shamir secret sharing over F_p (p prime).

Conventions:
- Party indices are non-zero field elements alpha_1, ..., alpha_M in F_p \\ {0}
  (we use α_i = i for i ∈ {1, ..., M}, requiring M < p)
- Threshold is t (degree of sharing polynomial).
- Reconstruct using any t+1 shares via Lagrange interpolation.

Used by:
- exp2_barrier: build the adversary matrix M ∈ F^(2c+1)×(2t+1)
- exp3_communication: nothing direct, but shares as a sanity check
"""

from typing import List, Tuple, Sequence
from . import polynomial as P
from . import field_arithmetic as F


def share(secret: int, t: int, num_parties: int, p: int, rng) -> List[Tuple[int, int]]:
    """
    Produce t-out-of-num_parties Shamir shares of `secret` over F_p.

    Returns list of (alpha_i, share_i) pairs, alpha_i = i for i in 1..num_parties.
    """
    if num_parties >= p:
        raise ValueError(f"num_parties {num_parties} must be < p {p}")
    if t < 0:
        raise ValueError("threshold must be >= 0")
    if t >= num_parties:
        raise ValueError(f"threshold t={t} must be < num_parties={num_parties}")
    secret = secret % p
    # uniform random poly of degree t with constant term = secret
    coeffs = [secret] + [rng.randrange(p) for _ in range(t)]
    return [(i, P.poly_eval(coeffs, i, p)) for i in range(1, num_parties + 1)]


def reconstruct(shares: Sequence[Tuple[int, int]], p: int) -> int:
    """Reconstruct secret from a list of (alpha_i, share_i) pairs (>= t+1 of them)."""
    if not shares:
        raise ValueError("no shares")
    xs = [s[0] for s in shares]
    ys = [s[1] for s in shares]
    poly = P.lagrange_interpolate(xs, ys, p)
    return P.poly_eval(poly, 0, p)


def random_shamir_polynomial(secret: int, t: int, p: int, rng) -> List[int]:
    """Polynomial p(X) of degree t with p(0) = secret, otherwise random."""
    secret = secret % p
    return [secret] + [rng.randrange(p) for _ in range(t)]
