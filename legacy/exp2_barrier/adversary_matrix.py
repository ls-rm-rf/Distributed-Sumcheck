"""
Experiment 2: build the adversary linear-system matrix.

V3 §4.2 unknown vector layout:
    x = (p_0, p_1, ..., p_t, d_1, d_2, ..., d_t)  in F^(2t+1)
    p(X) = p_0 + p_1*X + ... + p_t*X^t
    D(X) =        d_1*X + ... + d_t*X^t          (D(0) = 0 structurally)
    q(X) = p(X) + D(X)

Adversary equations (2c + 1):
    - c equations: p(alpha_i) = pHat_i        for i in I, |I| = c
    - c equations: q(alpha_i) = qHat_i        for i in I
    - 1 equation : p(0) = secret              (sum-claim row)

Matrix M in F^((2c+1) x (2t+1)):
    Row layout:
        rows 0   .. c-1   : p-equations  (Vandermonde over alpha_i, p-cols only)
        rows c   .. 2c-1  : q-equations  (Vandermonde p-cols + Vandermonde d-cols)
        row  2c           : p(0) = secret  -> e_0
    Column layout:
        cols 0   .. t     : p_0, ..., p_t  (p-coords)
        cols t+1 .. 2t    : d_1, ..., d_t  (D-coords; D(0)=0 structural)

Boundary set I is fixed to {1, 2, ..., c} subset of {1, ..., M}; this is
WLOG since rank only depends on the subset SIZE c, not the specific I,
so long as the alpha values are distinct.
"""

from typing import List, Tuple
from crypto_core import field_arithmetic as F


def p_indices(t: int) -> List[int]:
    """Column indices of (p_0, p_1, ..., p_t) in the unknown vector."""
    return list(range(t + 1))


def d_indices(t: int) -> List[int]:
    """Column indices of (d_1, d_2, ..., d_t) in the unknown vector."""
    return list(range(t + 1, 2 * t + 1))


def build_adversary_matrix(t: int, c: int, p: int) -> Tuple[List[List[int]], dict]:
    """
    Construct the (2c+1) x (2t+1) adversary matrix M as integer rows mod p.

    Args:
      t : sharing-poly degree   (also degree of D)
      c : boundary overlap size (0 <= c <= t)
      p : prime modulus

    Returns:
      (M, meta)
      meta = {
        "alpha": [list of corruption indices used as alpha_i],
        "p_cols": list, "d_cols": list,
        "row_layout": "p_eqs (c) | q_eqs (c) | secret_eq (1)",
        "shape": (2c+1, 2t+1),
      }
    """
    if not (0 <= c <= t):
        raise ValueError(f"need 0 <= c <= t, got c={c}, t={t}")
    if t + 1 >= p:
        raise ValueError(f"need p > t+1 for distinct alpha; got p={p}, t={t}")

    cols = 2 * t + 1
    p_cols = p_indices(t)        # 0..t
    d_cols = d_indices(t)        # t+1..2t

    alpha = list(range(1, c + 1))  # alpha_i = i, distinct nonzero in F_p

    rows: List[List[int]] = []

    # p-equations: p(alpha_i) = pHat_i  -->  sum_{k=0..t} alpha_i^k * p_k = ...
    for ai in alpha:
        row = [0] * cols
        # p-cols contribute (1, alpha_i, alpha_i^2, ..., alpha_i^t)
        ak = 1
        for k in range(t + 1):
            row[p_cols[k]] = ak
            ak = (ak * ai) % p
        rows.append(row)

    # q-equations: q(alpha_i) = qHat_i  -->  same p-Vandermonde + d-Vandermonde
    for ai in alpha:
        row = [0] * cols
        ak = 1
        for k in range(t + 1):
            row[p_cols[k]] = ak
            ak = (ak * ai) % p
        # d-cols contribute (alpha_i, alpha_i^2, ..., alpha_i^t)  (no d_0)
        ak = ai % p
        for k in range(t):
            row[d_cols[k]] = ak
            ak = (ak * ai) % p
        rows.append(row)

    # secret row: p(0) = secret  -->  e_0
    # PER V3 §4.2 parenthetical: this row is ONLY added in the c == t case,
    # to test "full recovery given the secret". For c < t we have only the
    # 2c share equations, which yields the V3 §4.5 predictions:
    #     c < t : secret_rec = 0, poly_rec = 0, residual_dim = t - c
    #     c = t : secret_rec = 1, poly_rec = 1, residual_dim = 0
    if c == t:
        sec_row = [0] * cols
        sec_row[0] = 1
        rows.append(sec_row)

    meta = {
        "alpha": alpha,
        "p_cols": p_cols,
        "d_cols": d_cols,
        "row_layout": ("p_eqs (c) | q_eqs (c) | secret_eq (1)"
                       if c == t else
                       "p_eqs (c) | q_eqs (c)   [no secret_eq because c < t]"),
        "shape": (len(rows), cols),
        "secret_eq_included": (c == t),
    }
    return rows, meta
