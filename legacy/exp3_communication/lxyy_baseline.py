"""
LXYY (Liu-Xie-Yu-Yu) online-verify baseline (V3 §6.3 sign-off).

Per-party online verification reconstruction units:
    lxyy_verify_per_party(n) = 4*n + 6                (units of |F|)

This is the single-round equivalent baseline used to compute
'overhead_ratio' for refresh schemes.

Reference: V3 spec, advisor sign-off "LXYY baseline 4n+6 per-party".
"""


def lxyy_verify_per_party(n: int) -> int:
    """Online-verify per-party reconstruction cost (units of |F|), per V3 sign-off."""
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    return 4 * n + 6


def lxyy_verify_total(M: int, n: int) -> int:
    """Sum across all M parties."""
    return M * lxyy_verify_per_party(n)
