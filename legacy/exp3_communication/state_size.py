"""
Per-round state-size formulas (V3 §6.1).

For an n-variable deg-3 sumcheck with refreshable proof state at round k:

    d_k_table(n, k)  = 2 * 2^(n - k)              (multilinear table size)
    d_k_mask(n, k)   = 3 * (n - k) + 2 for k<n; 0 at terminal k=n
    d_k_total(n, k)  = d_k_table + d_k_mask       (per-party state to refresh)

Special boundary values (V3 §6.2):
    d_k_full(n)      = 3*n + 3                    (full mask space, no kernel)
    d_k_kernel(n, k) = 3*(n - k) + 2              (kernel-only mask)

These are the per-party UNITS counted in field elements |F|.
All multiplications elsewhere produce communication in field elements.
"""


def d_k_table(n: int, k: int) -> int:
    if not (0 <= k <= n):
        raise ValueError(f"need 0 <= k <= n; got k={k}, n={n}")
    return 2 * (2 ** (n - k))


def d_k_mask(n: int, k: int) -> int:
    if not (0 <= k <= n):
        raise ValueError(f"need 0 <= k <= n; got k={k}, n={n}")
    # The terminal transcript determines every mask coefficient.
    return 0 if k == n else 3 * (n - k) + 2


def d_k_total(n: int, k: int) -> int:
    return d_k_table(n, k) + d_k_mask(n, k)


def d_k_full(n: int) -> int:
    """Full mask coordinate space (no kernel reduction)."""
    return 3 * n + 3


def d_k_kernel(n: int, k: int) -> int:
    """Kernel-restricted mask at round k -- equals d_k_mask."""
    return d_k_mask(n, k)
