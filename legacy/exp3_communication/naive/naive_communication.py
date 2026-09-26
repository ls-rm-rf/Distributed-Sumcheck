"""
Naive 'every party reshares to every other' refresh (V3 §6.4).

Each of the M parties freshly Shamir-shares its current state to all M-1
other parties. Per-party communication therefore scales linearly with
state size and parties:

    naive_per_party(M, D_k) = D_k * (M - 1)
    naive_total(M, D_k)     = M * naive_per_party = M * (M-1) * D_k

CSV note: schemes report BOTH per_party and total via the
`accounting_scope` column.
"""


def naive_per_party(M: int, D_k: int) -> int:
    if M < 2:
        raise ValueError(f"need M >= 2; got {M}")
    return D_k * (M - 1)


def naive_total(M: int, D_k: int) -> int:
    return M * naive_per_party(M, D_k)
