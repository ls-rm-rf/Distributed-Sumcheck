"""
Exact modular field arithmetic over F_p.

All operations:
- Take Python ints in [0, p-1] (or normalize to that range)
- Return ints in [0, p-1]
- Never use floats

Vectors are Python lists of ints. Matrices are lists of lists.
"""

from typing import List, Sequence


def normalize(a: int, p: int) -> int:
    return a % p


def add(a: int, b: int, p: int) -> int:
    return (a + b) % p


def sub(a: int, b: int, p: int) -> int:
    return (a - b) % p


def neg(a: int, p: int) -> int:
    return (-a) % p


def mul(a: int, b: int, p: int) -> int:
    return (a * b) % p


def pow_mod(a: int, e: int, p: int) -> int:
    return pow(a % p, e, p)


def inv(a: int, p: int) -> int:
    """Multiplicative inverse via Fermat's little theorem (p prime)."""
    a = a % p
    if a == 0:
        raise ZeroDivisionError(f"inverse of 0 in F_{p}")
    return pow(a, p - 2, p)


def div(a: int, b: int, p: int) -> int:
    return mul(a, inv(b, p), p)


# -------- vector ops --------

def vec_add(u: Sequence[int], v: Sequence[int], p: int) -> List[int]:
    if len(u) != len(v):
        raise ValueError(f"length mismatch {len(u)} vs {len(v)}")
    return [(a + b) % p for a, b in zip(u, v)]


def vec_sub(u: Sequence[int], v: Sequence[int], p: int) -> List[int]:
    if len(u) != len(v):
        raise ValueError(f"length mismatch {len(u)} vs {len(v)}")
    return [(a - b) % p for a, b in zip(u, v)]


def vec_scale(c: int, v: Sequence[int], p: int) -> List[int]:
    c = c % p
    return [(c * x) % p for x in v]


def vec_dot(u: Sequence[int], v: Sequence[int], p: int) -> int:
    if len(u) != len(v):
        raise ValueError(f"length mismatch {len(u)} vs {len(v)}")
    s = 0
    for a, b in zip(u, v):
        s = (s + a * b) % p
    return s


# -------- matrix ops --------

def mat_dims(M: Sequence[Sequence[int]]):
    rows = len(M)
    cols = len(M[0]) if rows > 0 else 0
    for r in M:
        if len(r) != cols:
            raise ValueError("ragged matrix")
    return rows, cols


def mat_mul(A, B, p: int) -> List[List[int]]:
    ra, ca = mat_dims(A)
    rb, cb = mat_dims(B)
    if ca != rb:
        raise ValueError(f"shapes incompatible: ({ra},{ca}) x ({rb},{cb})")
    out = [[0] * cb for _ in range(ra)]
    for i in range(ra):
        Ai = A[i]
        for j in range(cb):
            s = 0
            for k in range(ca):
                s = (s + Ai[k] * B[k][j]) % p
            out[i][j] = s
    return out


def mat_vec(A, v, p: int) -> List[int]:
    ra, ca = mat_dims(A)
    if ca != len(v):
        raise ValueError(f"shape mismatch ({ra},{ca}) * {len(v)}")
    return [sum(A[i][k] * v[k] for k in range(ca)) % p for i in range(ra)]


def normalize_matrix(M, p: int) -> List[List[int]]:
    return [[x % p for x in row] for row in M]
