"""
Experiment 1: round-k transcript constraint matrix C_k construction.

Faithful implementation of the construction from the paper (Sections 4.4-4.5,
Lemma "Rank saturation"):

  Mask polynomial:
      g(Y_1,...,Y_n) = g_0 + sum_{i=1}^n sum_{m=1}^3 g_{i,m} Y_i^m
                            + g_{n,4} Y_n^4 + g_{n,5} Y_n^5

  Coefficient vector  gamma in F^{3n+3}, ordered:
      [g_0, g_{1,1}, g_{1,2}, g_{1,3}, g_{2,1}, ..., g_{n-1,3},
            g_{n,1}, g_{n,2}, g_{n,3}, g_{n,4}, g_{n,5}]

  For 0 <= k <= n-1 (ordinary rounds):
      C_k consists of
        - 1 initial-claim row G = sum_{y in {0,1}^n} g(y)
        - 4 coefficient rows (in X) of each H_j for j = 1..k
              H_j(X) = sum_{y_{j+1},...,y_n in {0,1}}
                       g(r_1,...,r_{j-1}, X, y_{j+1},...,y_n)

  For k = n (terminal round j=n):
      C_k additionally contains the 6 coefficient rows of H_n.

Lemma 4.4 (paper):
    rank(C_k) = 1 + 3k    for 0 <= k <= n-1
    rank(C_n) = 3n + 3    after the terminal round

The rank pattern follows from a *chain relation*
    H_{j-1}(r_{j-1}) = H_j(0) + H_j(1)
which makes the constant-in-X coefficient row of H_j linearly dependent on
the previous round's rows. The 3 (resp. 5 in terminal) nonconstant rows of
H_j are pure scaled standard basis vectors  2^{n-j} e_{(j,m)}  on FRESH
coordinates, hence independent of all earlier rows; this is why Lemma 4.4
holds for ANY challenge values (including r in {0,1}), provided |F| is odd
so that the scalar 2^{n-j} is invertible.

Sanity check (paper Example 4.5, n=3):
    G       = 8 g_0 + 4 (S_1 + S_2 + S_3)              (rank 1)
    H_1(X)  = 4 g_0 + 4 P_1(X) + 2 S_2 + 2 S_3         (rank 1->4)
    H_2(X)  = 2 g_0 + 2 P_1(r_1) + 2 P_2(X) + S_3      (rank 4->7)
    H_3(X)  = g_0 + P_1(r_1) + P_2(r_2) + P_3(X)       (rank 7->12)
    P_i(X)  = g_{i,1} X + g_{i,2} X^2 + g_{i,3} X^3
    P_n(X)  also has g_{n,4} X^4 + g_{n,5} X^5
    S_i     = P_i(1)
"""

from typing import List, Sequence


def gamma_dim(n: int) -> int:
    """Total dimension of gamma is always 3n + 3 (paper §4.4)."""
    return 3 * n + 3


def index_g0() -> int:
    return 0


def index_g(j: int, m: int, n: int) -> int:
    """
    Index of g_{j,m} in gamma.

      j in {1..n}
      m in {1,2,3}        for j < n
      m in {1,2,3,4,5}    for j = n
    """
    if not (1 <= j <= n):
        raise ValueError(f"j must be in {{1,...,n={n}}}, got {j}")
    if j < n and m not in (1, 2, 3):
        raise ValueError(f"for j<n, m must be in {{1,2,3}}, got {m}")
    if j == n and m not in (1, 2, 3, 4, 5):
        raise ValueError(f"for j=n, m must be in {{1..5}}, got {m}")
    return 1 + 3 * (j - 1) + (m - 1)


def expected_rank(k: int, n: int) -> int:
    """
    Lemma 4.4 (paper):
      rank(C_k) = 1 + 3k          for 0 <= k <= n-1
      rank(C_n) = 3n + 3          for the terminal round.
    """
    if not (0 <= k <= n):
        raise ValueError(f"k must be in [0, n={n}], got {k}")
    if k < n:
        return 1 + 3 * k
    return 3 * n + 3


def _initial_claim_row(n: int, p: int, cols: int) -> List[int]:
    """
    Coefficient row of G = sum_{y in {0,1}^n} g(y)  in gamma.

    On gamma:
      coeff(g_0)         = 2^n               (every y contributes g_0)
      coeff(g_{i,m})     = 2^{n-1}           for i in {1..n-1}, m in {1,2,3}
                                              (number of y's with y_i = 1)
      coeff(g_{n,m})     = 2^{n-1}           for m in {1..5}
    """
    row = [0] * cols
    row[index_g0()] = pow(2, n, p)
    half = pow(2, n - 1, p)
    for i in range(1, n):
        for m in (1, 2, 3):
            row[index_g(i, m, n)] = half
    for m in (1, 2, 3, 4, 5):
        row[index_g(n, m, n)] = half
    return row


def _ordinary_round_rows(j: int, n: int, challenges: Sequence[int],
                         p: int, cols: int) -> List[List[int]]:
    """
    The 4 coefficient rows c_0, c_1, c_2, c_3 of H_j (1 <= j <= n-1):
        H_j(X) = c_0 + c_1 X + c_2 X^2 + c_3 X^3

    Coefficients (paper §4.4):
      c_0 (the constant-in-X row):
          2^{n-j}            on g_0
          2^{n-j} * r_i^m    on g_{i,m}        for 1 <= i < j, m in {1,2,3}
          2^{n-j-1}          on g_{i,m}        for j < i < n, m in {1,2,3}
          2^{n-j-1}          on g_{n,m}        for m in {1,2,3,4,5}
      c_l (the X^l row), l = 1, 2, 3:
          2^{n-j}            on g_{j,l}        (everything else 0)
    """
    pow2_nj   = pow(2, n - j, p)
    pow2_nj_1 = pow(2, n - j - 1, p) if (n - j - 1) >= 0 else 0

    # constant-in-X row
    c0 = [0] * cols
    c0[index_g0()] = pow2_nj
    for i in range(1, j):
        ri = challenges[i - 1] % p
        for m in (1, 2, 3):
            c0[index_g(i, m, n)] = (pow2_nj * pow(ri, m, p)) % p
    # i in {j+1, ..., n-1}
    for i in range(j + 1, n):
        for m in (1, 2, 3):
            c0[index_g(i, m, n)] = pow2_nj_1
    # i = n  (degrees 1..5)
    for m in (1, 2, 3, 4, 5):
        c0[index_g(n, m, n)] = pow2_nj_1

    rows = [c0]
    # nonconstant rows c_1, c_2, c_3
    for l in (1, 2, 3):
        row = [0] * cols
        row[index_g(j, l, n)] = pow2_nj
        rows.append(row)
    return rows


def _terminal_round_rows(n: int, challenges: Sequence[int],
                         p: int, cols: int) -> List[List[int]]:
    """
    The 6 coefficient rows of H_n (terminal, degree 5):
        H_n(X) = g_0 + sum_{i<n} sum_{m=1..3} g_{i,m} r_i^m
                     + g_{n,1} X + g_{n,2} X^2 + g_{n,3} X^3
                     + g_{n,4} X^4 + g_{n,5} X^5

    Coefficient rows c_0, c_1, ..., c_5 in X:
      c_0:  1 on g_0;   r_i^m on g_{i,m} for i<n, m=1..3
      c_l (l=1..5):  1 on g_{n,l}
    """
    c0 = [0] * cols
    c0[index_g0()] = 1
    for i in range(1, n):
        ri = challenges[i - 1] % p
        for m in (1, 2, 3):
            c0[index_g(i, m, n)] = pow(ri, m, p)

    rows = [c0]
    for l in (1, 2, 3, 4, 5):
        row = [0] * cols
        row[index_g(n, l, n)] = 1
        rows.append(row)
    return rows


def build_C_k(n: int,
              k: int,
              challenges: Sequence[int],
              p: int) -> List[List[int]]:
    """
    Construct the round-k transcript constraint matrix C_k over F_p,
    faithful to paper §4.4 Lemma "Rank saturation".

    Args:
      n          : total number of sumcheck rounds (>= 1)
      k          : current round index, 0 <= k <= n
      challenges : list of k challenges r_1, ..., r_k in F_p
      p          : odd prime modulus

    Returns:
      C_k as a list of rows of integers mod p.
      Number of rows:
        k = 0           : 1
        1 <= k <= n - 1 : 1 + 4 * k
        k = n           : 1 + 4 * (n - 1) + 6  =  4n + 3

    Paper Lemma 4.4:
      rank(C_k) = 1 + 3k      for 0 <= k <= n-1
      rank(C_n) = 3n + 3      after the terminal round.

    The construction is challenge-tolerant (Lemma 4.4 holds for any
    r_1,...,r_k in F_p, including {0, 1}) provided |F_p| is odd
    (so that 2^{n-j} is invertible).
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if k < 0 or k > n:
        raise ValueError(f"k must be in [0, n={n}], got {k}")
    if len(challenges) != k:
        raise ValueError(f"need exactly k={k} challenges, got {len(challenges)}")
    if p % 2 == 0:
        raise ValueError(f"need odd prime; got p={p}")

    cols = gamma_dim(n)
    rows: List[List[int]] = [_initial_claim_row(n, p, cols)]

    if k == 0:
        return rows

    # Ordinary rounds j = 1..min(k, n-1)
    upper = k if k <= n - 1 else (n - 1)
    for j in range(1, upper + 1):
        rows.extend(_ordinary_round_rows(j, n, challenges, p, cols))

    # Terminal round j = n  (only when k == n)
    if k == n:
        rows.extend(_terminal_round_rows(n, challenges, p, cols))

    return rows


def is_degenerate_challenge(r: int, p: int) -> bool:
    """
    Metadata helper: a challenge is *flagged* as degenerate iff r mod p in {0, 1}.

    NOTE (paper construction): with the faithful paper construction, NO
    challenge value is degenerate w.r.t. Lemma 4.4 - the rank stays at
    1 + 3k for any r including {0, 1}. This flag is retained purely for
    the CSV's `degenerate_challenge_count` metadata column to track how
    often boundary-edge challenge values appear. In stress mode
    (forced_01) every challenge is "flagged".
    """
    return (r % p) in (0, 1)
