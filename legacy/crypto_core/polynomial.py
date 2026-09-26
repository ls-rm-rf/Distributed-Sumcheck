"""
Polynomials over F_p represented as coefficient lists [c0, c1, ..., cd]
where c0 is the constant term.
"""

from typing import List, Sequence
from . import field_arithmetic as F


Poly = List[int]


def poly_normalize(coeffs: Sequence[int], p: int) -> Poly:
    """Reduce coeffs mod p and strip trailing zeros (keep [0] for zero poly)."""
    out = [c % p for c in coeffs]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def poly_eval(coeffs: Sequence[int], x: int, p: int) -> int:
    """Horner evaluation of poly at x ∈ F_p."""
    x = x % p
    s = 0
    for c in reversed(coeffs):
        s = (s * x + c) % p
    return s


def poly_add(a: Sequence[int], b: Sequence[int], p: int) -> Poly:
    n = max(len(a), len(b))
    out = [0] * n
    for i, c in enumerate(a):
        out[i] = (out[i] + c) % p
    for i, c in enumerate(b):
        out[i] = (out[i] + c) % p
    return poly_normalize(out, p)


def poly_sub(a: Sequence[int], b: Sequence[int], p: int) -> Poly:
    n = max(len(a), len(b))
    out = [0] * n
    for i, c in enumerate(a):
        out[i] = (out[i] + c) % p
    for i, c in enumerate(b):
        out[i] = (out[i] - c) % p
    return poly_normalize(out, p)


def poly_mul(a: Sequence[int], b: Sequence[int], p: int) -> Poly:
    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            out[i + j] = (out[i + j] + ai * bj) % p
    return poly_normalize(out, p)


def poly_scale(c: int, a: Sequence[int], p: int) -> Poly:
    c = c % p
    return poly_normalize([(c * x) % p for x in a], p)


def poly_zero() -> Poly:
    return [0]


def random_poly(degree: int, p: int, rng) -> Poly:
    """Uniformly random polynomial of exact degree `degree` (leading coeff != 0)."""
    coeffs = [rng.randrange(p) for _ in range(degree + 1)]
    if degree >= 1:
        while coeffs[-1] == 0:
            coeffs[-1] = rng.randrange(p)
    return coeffs


def random_poly_at_most(degree: int, p: int, rng) -> Poly:
    """Uniformly random polynomial of degree at most `degree`."""
    return [rng.randrange(p) for _ in range(degree + 1)]


def vandermonde_row(x: int, num_cols: int, p: int) -> List[int]:
    """[1, x, x^2, ..., x^{num_cols-1}] mod p."""
    x = x % p
    row = [1] * num_cols
    for i in range(1, num_cols):
        row[i] = (row[i - 1] * x) % p
    return row


def lagrange_interpolate(points: Sequence[int],
                         values: Sequence[int],
                         p: int) -> Poly:
    """
    Unique polynomial of degree < len(points) passing through (points[i], values[i]).
    Points must be distinct mod p.
    """
    if len(points) != len(values):
        raise ValueError("points/values length mismatch")
    n = len(points)
    pts = [x % p for x in points]
    if len(set(pts)) != n:
        raise ValueError("points must be distinct mod p")
    result: Poly = [0]
    for i in range(n):
        # build L_i(X) = ∏_{j≠i} (X - x_j) / (x_i - x_j)
        Li: Poly = [1]
        denom = 1
        for j in range(n):
            if i == j:
                continue
            # multiply Li by (X - x_j)
            new = [0] * (len(Li) + 1)
            for k, c in enumerate(Li):
                new[k] = (new[k] - c * pts[j]) % p
                new[k + 1] = (new[k + 1] + c) % p
            Li = new
            denom = (denom * (pts[i] - pts[j])) % p
        invd = F.inv(denom, p)
        scaled = [(c * values[i] % p) * invd % p for c in Li]
        result = poly_add(result, scaled, p)
    return poly_normalize(result, p)
