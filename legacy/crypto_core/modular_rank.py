"""
Exact modular Gaussian elimination over F_p (p prime).

Provides:
- rank(M, p): rank by row reduction
- rref(M, p): reduced row echelon form + pivot columns
- kernel_basis(M, p): basis of {x : M x = 0}
- projected_nullity(M, indices, p): dim Π_S(ker M)
                                    where Π_S projects onto coordinates in `indices`

These functions support the corrected V3 judgments:
  polynomial_recoverable ⇔ projected_nullity(M, p_indices, p) == 0
  secret_recoverable     ⇔ projected_nullity(M, [p0_index], p) == 0
  residual_transition_dim = projected_nullity_via_basis(M, D_indices, p)
"""

from typing import List, Sequence, Tuple
from . import field_arithmetic as F


Matrix = List[List[int]]


def _copy(M: Sequence[Sequence[int]], p: int) -> Matrix:
    return [[x % p for x in row] for row in M]


def rref(M: Sequence[Sequence[int]], p: int) -> Tuple[Matrix, List[int]]:
    """
    Reduced row echelon form modulo p.

    Returns (R, pivots) where R is RREF and pivots is the list of
    pivot column indices (in row order).
    """
    A = _copy(M, p)
    if not A:
        return A, []
    rows, cols = len(A), len(A[0])
    pivots: List[int] = []
    r = 0
    for c in range(cols):
        if r >= rows:
            break
        # find a pivot in column c at or below row r
        pivot = -1
        for i in range(r, rows):
            if A[i][c] % p != 0:
                pivot = i
                break
        if pivot == -1:
            continue
        # swap
        if pivot != r:
            A[r], A[pivot] = A[pivot], A[r]
        # normalize pivot row
        invp = F.inv(A[r][c], p)
        A[r] = [(x * invp) % p for x in A[r]]
        # eliminate other rows
        for i in range(rows):
            if i == r:
                continue
            f = A[i][c] % p
            if f != 0:
                A[i] = [(A[i][j] - f * A[r][j]) % p for j in range(cols)]
        pivots.append(c)
        r += 1
    return A, pivots


def rank(M: Sequence[Sequence[int]], p: int) -> int:
    """Rank of M over F_p."""
    if not M:
        return 0
    _, pivots = rref(M, p)
    return len(pivots)


def kernel_basis(M: Sequence[Sequence[int]], p: int, cols: int = None) -> Matrix:
    """
    Basis of ker(M) = { x in F_p^n : M x = 0 } as a list of vectors.

    Returns a list of length-n integer vectors. Number of vectors = nullity(M).

    If M is an empty list of rows, `cols` MUST be supplied so the function
    can return the full identity basis of F_p^cols.
    """
    if not M:
        if cols is None:
            return []
        # No constraints -> kernel = full space F_p^cols
        return [[1 if i == j else 0 for j in range(cols)] for i in range(cols)]
    rows, ncols = len(M), len(M[0])
    if cols is not None and cols != ncols:
        raise ValueError(f"cols hint {cols} != actual matrix width {ncols}")
    R, pivots = rref(M, p)
    pivot_set = set(pivots)
    free_cols = [c for c in range(ncols) if c not in pivot_set]
    basis: Matrix = []
    pivot_row = {pivots[i]: i for i in range(len(pivots))}
    for fc in free_cols:
        v = [0] * ncols
        v[fc] = 1
        for c in pivots:
            r_idx = pivot_row[c]
            v[c] = (-R[r_idx][fc]) % p
        basis.append(v)
    return basis


def projected_nullity(M: Sequence[Sequence[int]],
                      indices: Sequence[int],
                      p: int,
                      cols: int = None) -> int:
    """
    Compute dim Pi_S(ker M), where Pi_S projects a vector onto the
    coordinates listed in `indices`.

    If M is empty (no rows), pass `cols` so the kernel is treated as F_p^cols.
    """
    B = kernel_basis(M, p, cols=cols)
    if not B:
        return 0
    sub = [[v[i] for v in B] for i in indices]
    if not sub or not sub[0]:
        return 0
    return rank(sub, p)


# ---------- equivalence form sanity ----------

def stacked_rank_difference(M: Sequence[Sequence[int]],
                            indices: Sequence[int],
                            p: int,
                            cols: int = None) -> int:
    """
    Equivalent form: rank([M; Pi_indices]) - rank(M),
    where Pi_indices stacks the standard-basis rows e_i^T for i in indices.

    polynomial_recoverable  ⇔  projected_nullity(M, p_indices, p) == 0
                            ⇔  rank([M; Pi_p]) - rank(M) == 0

    `cols` must be provided if M is empty.
    """
    if not M:
        if cols is None:
            return 0
        # rank(M) = 0; rank of |indices| distinct e_i rows = number of distinct indices
        return len(set(indices))
    ncols = len(M[0])
    if cols is not None and cols != ncols:
        raise ValueError(f"cols hint {cols} != actual matrix width {ncols}")
    rM = rank(M, p)
    extra = []
    for i in indices:
        row = [0] * ncols
        row[i] = 1
        extra.append(row)
    stacked = list(M) + extra
    return rank(stacked, p) - rM
